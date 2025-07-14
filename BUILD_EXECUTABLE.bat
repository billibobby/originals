@echo off
REM ============================================================================
REM The Originals - Easy Executable Builder Launcher
REM Double-click this file to build your shareable executable!
REM ============================================================================

echo.
echo ====================================================
echo   THE ORIGINALS - EASY EXECUTABLE BUILDER
echo ====================================================
echo.
echo 🎮 Creating a shareable version of The Originals!
echo.
echo This will build a standalone .exe file that you can
echo share with friends - they won't need Python!
echo.

REM Run the build script
call "build_scripts\build_exe.bat"

echo.
echo 🎉 Build process complete!
echo.
echo If the build was successful, you now have a shareable
echo package in dist\TheOriginals_Package\ that you can
echo zip and share with friends!
echo. 