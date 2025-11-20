@ECHO OFF
ECHO Welcome to the MADDEN 09 ISO MOD CREATION TOOL (lite version)
ECHO.
TIMEOUT /T 0 /NOBREAK >NUL

:start
ECHO Checking if installation files are in the correct folder...
IF NOT EXIST "MOD\SLUS_217.70" (
  ECHO The Installation Files are not in the correct folders. Please re-read the instructions and try again!
  TIMEOUT /T 0 /NOBREAK >NUL
  EXIT /B 1
)
IF NOT EXIST "*.ISO" (
  ECHO A copy of the MADDEN 09 Football ISO Game is missing.
  TIMEOUT /T 0 /NOBREAK >NUL
  EXIT /B 1
)
IF NOT EXIST "IMGBURN.EXE" (
  ECHO IMGBURN.EXE is missing. Please place it here.
  TIMEOUT /T 0 /NOBREAK >NUL
  EXIT /B 1
)

:install
ECHO Copying mods into the "next" folder, preserving existing files...
TIMEOUT /T 0 /NOBREAK >NUL

REM ── Ensure the “next” folder exists
IF NOT EXIST "next" (
  mkdir "next"
)

REM ── Fast, multi-threaded merge: copy mod/* into next/* without deleting extras
robocopy "mod" "next" /E /MT:16 /NFL /NDL /NJH /NJS >NUL

cd next
ECHO.
ECHO Installation File Location: Correct.
ECHO Deleting QKL files...
del "DATA\*.qkl" /Q
ECHO Deleting ONLINE leftovers...
rmdir /S /Q "NETGUI" "EACN" "ONLINE"
ECHO Deleting leftover .DAT files...
del "DATA\CAFE*.DAT" "DATA\ONLINE.DAT" "DATA\OSDKSTRN.DAT" "DATA\UIONLINE.DAT" /Q
ECHO Deleting backup and index files...
del "*.bak" /S /Q
del "*.xdb" /S /Q
TIMEOUT /T 0 /NOBREAK >NUL

ECHO Patching Complete!
ECHO.
ECHO Launching ImgBurn to build the modded ISO...
cd ..
TIMEOUT /T 0 /NOBREAK >NUL

REM ── Wait for ImgBurn to finish before continuing
START "" /WAIT "ImgBurn.exe" ^
  /MODE BUILD ^
  /SRC "next" ^
  /DEST "Madden 09 Mod.iso" ^
  /VOLUMELABEL "MADDEN 09 MOD" ^
  /ROOTFOLDER YES ^
  /NOIMAGEDETAILS YES ^
  /START ^
  /OVERWRITE YES ^
  /CLOSE

ECHO Madden 09 MOD ISO successfully created!
ECHO.
ECHO Press any key to exit, or it will close automatically in 10 seconds...
TIMEOUT /T 10 >NUL
EXIT /B 0
