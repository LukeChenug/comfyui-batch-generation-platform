# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend/src/simple_main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('index.html', '.'), ('runner_v0.2.html', '.'), ('batch_generation_dashboard.html', '.'), ('backend/src/scenes', 'backend/src/scenes')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'engineio.async_drivers.aiohttp', 'sqlite3', 'backend.src.routes.task_routes', 'backend.src.services.task_service', 'backend.src.services.workflow_service', 'backend.src.database.db', 'backend.src.auth', 'backend.src.jobs.runner', 'backend.src.init_admin'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Runner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
