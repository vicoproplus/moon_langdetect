@echo off
"C:\Users\Administrator\.moon\bin\moon.exe" run --target wasm-gc cmd/main > run_wasm.out 2> run_wasm.err
echo %ERRORLEVEL%> run_wasm.rc
