// Run the actual patched PX4 functions with fault-injected hardware interfaces.
#include <cassert>
#include <cerrno>
#include <cstdint>

#define OK 0
#define FAR
#define MTDIOC_GEOMETRY 1
#define PX4_ERR(...) ((void)0)

struct mtd_geometry_s { unsigned long blocksize, erasesize, neraseblocks; };
struct spi_dev_s {};
struct mtd_dev_s { int (*ioctl)(mtd_dev_s *, int, unsigned long); };
struct mtd_instance_s { int devid; mtd_dev_s *mtd_dev; unsigned n_partitions_current; };

static int geometry_result = 0;
static int get_geometry(mtd_dev_s *, int, unsigned long arg)
{
	if (geometry_result) { return geometry_result; }
	*reinterpret_cast<mtd_geometry_s *>(arg) = {256, 4096, 4096};
	return 0;
}
static mtd_dev_s chip{get_geometry};
#if defined(CONFIG_MTD_W25)
static spi_dev_s bus;
static bool bus_present = true;
static bool chip_present = true;
static int px4_find_spi_bus(int devid) { assert(devid == 7); return 3; }
static spi_dev_s *px4_spibus_initialize(int number) { assert(number == 3); return bus_present ? &bus : nullptr; }
static mtd_dev_s *w25_initialize(spi_dev_s *spi) { assert(spi == &bus); return chip_present ? &chip : nullptr; }
#endif

#include "mtd_functions.inc"

int main()
{
	mtd_instance_s instance{7, nullptr, 0};
#if defined(CONFIG_MTD_W25)
	assert(spi_nor_attach(instance) == 0);
	assert(instance.mtd_dev == &chip);
	instance.mtd_dev = nullptr;
	bus_present = false;
	assert(spi_nor_attach(instance) == -ENXIO);
	assert(instance.mtd_dev == nullptr);
	bus_present = true;
	chip_present = false;
	assert(spi_nor_attach(instance) == -ENODEV);
	assert(instance.mtd_dev == nullptr);
#else
	assert(spi_nor_attach(instance) == -ENXIO);
#endif
	instance.mtd_dev = &chip;
	unsigned long blocksize, erasesize, neraseblocks;
	unsigned blocks_per_erase, blocks, size;
	assert(px4_mtd_get_geometry(&instance, &blocksize, &erasesize, &neraseblocks,
				   &blocks_per_erase, &blocks, &size) == 0);
	assert(blocksize == 256 && erasesize == 4096 && blocks_per_erase == 16);
	assert(size == 16 * 1024 * 1024); // No divide-by-zero before the first partition.
	instance.n_partitions_current = 2;
	assert(px4_mtd_get_geometry(&instance, &blocksize, &erasesize, &neraseblocks,
				   &blocks_per_erase, &blocks, &size) == 0);
	assert(size == 8 * 1024 * 1024);
	geometry_result = -EIO;
	assert(px4_mtd_get_geometry(&instance, &blocksize, &erasesize, &neraseblocks,
				   &blocks_per_erase, &blocks, &size) == -EIO);
}
