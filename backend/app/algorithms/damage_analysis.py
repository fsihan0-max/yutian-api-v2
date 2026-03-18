from typing import Any, Dict


def run_damage_analysis(request_data: Dict[str, Any]) -> Dict[str, Any]:
    # Lazy import: avoid binding API layer to legacy Flask handlers while reusing mature math pipeline.
    from . import legacy_engine

    geometry = request_data["geometry"]
    area_mu = float(request_data.get("area_mu", 0) or 0)
    crop_mode = str(request_data.get("crop_mode", "wheat") or "wheat")
    model_mode = str(request_data.get("model_mode", "rule") or "rule")
    file_bytes = request_data.get("file_bytes")

    if crop_mode not in legacy_engine.CROP_CONFIGS:
        crop_mode = "wheat"
    if model_mode not in {"rule", "ml"}:
        model_mode = "rule"

    if file_bytes:
        engine_type = "用户提供: 无人机高分影像"
        image_date = "用户实时上传"
        with legacy_engine.MemoryFile(file_bytes) as memfile:
            with memfile.open() as dataset:
                tiff_crs = dataset.crs
                reprojected_poly = legacy_engine.transform_geom("EPSG:4326", tiff_crs, geometry)
                out_image, _ = legacy_engine.mask(dataset, [reprojected_poly], crop=True)
                bands = legacy_engine.extract_drone_bands(dataset, out_image)
    else:
        engine_type = "云端直连: Sentinel-2"
        bands, image_date = legacy_engine.fetch_stac_bands(geometry)

    return legacy_engine.assemble_analysis_result(
        bands=bands,
        area_mu=area_mu,
        engine_type=engine_type,
        image_date=image_date,
        crop_mode=crop_mode,
        model_mode=model_mode,
    )
