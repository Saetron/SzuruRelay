from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.timing import TimingControl

admin_router = APIRouter()


@admin_router.post("/admin/timing/enable")
async def enable_timing():
    """Enable performance timing logs"""
    TimingControl.enable()
    return JSONResponse(
        {"message": "Timing logs enabled", "status": "enabled"}, status_code=200
    )


@admin_router.post("/admin/timing/disable")
async def disable_timing():
    """Disable performance timing logs"""
    TimingControl.disable()
    return JSONResponse(
        {"message": "Timing logs disabled", "status": "disabled"}, status_code=200
    )


@admin_router.post("/admin/timing/toggle")
async def toggle_timing():
    """Toggle performance timing logs status"""
    TimingControl.toggle()
    status = "enabled" if TimingControl.status() else "disabled"
    return JSONResponse(
        {"message": f"Timing logs {status}", "status": status}, status_code=200
    )


@admin_router.get("/admin/timing/status")
async def timing_status():
    """Get performance timing logs status"""
    status = "enabled" if TimingControl.status() else "disabled"
    return JSONResponse({"status": status}, status_code=200)
