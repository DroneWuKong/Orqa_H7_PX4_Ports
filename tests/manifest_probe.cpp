#include <cassert>
#include <cstring>
#include <board_config.h>
#include <px4_platform_common/px4_manifest.h>

int main()
{
	const auto *manifest = board_get_manifest();
	assert(manifest->nmft == 1 && manifest->mfts[0]->type == MTD);
	const auto *mtd = static_cast<const px4_mtd_manifest_t *>(manifest->mfts[0]->pmft);
	assert(mtd->nconfigs == 1);
	const auto *flash = mtd->entries[0];
	assert(flash->device->bus_type == px4_mft_device_t::SPI_NOR);
#if defined(FLASH_BASED_PARAMS)
	assert(flash->npart == 1); // H7 calibration must stay in internal flash.
	const unsigned mission = 0;
#else
	assert(flash->npart == 2);
	assert(flash->partd[0].type == MTD_PARAMETERS);
	assert(std::strcmp(flash->partd[0].path, "/fs/mtd_params") == 0);
	assert(flash->partd[0].nblocks * 256 == 65536);
	const unsigned mission = 1;
#endif
	assert(flash->partd[mission].type == MTD_WAYPOINTS);
	assert(std::strcmp(flash->partd[mission].path, "/fs/mtd_waypoints") == 0);
	assert(flash->partd[mission].nblocks * 256 == 262144);
	unsigned total_bytes = 0;
	for (unsigned i = 0; i < flash->npart; ++i) {
		const unsigned bytes = flash->partd[i].nblocks * 256;
		assert(bytes % 4096 == 0);
		total_bytes += bytes;
	}
	assert(total_bytes <= 16 * 1024 * 1024);
}
