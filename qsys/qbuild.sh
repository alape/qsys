#!/bin/bash

BUILD_FOLDER="build"
QSIM_CONFIG="../qas/emulation/configs/modern.json"
QAS="../qas/qas.py"
QSIM="../qas/qsim.py"

LLR_FONT="tools/bitfont/Ac437_HP_150_re.ttf"
LLR_SOURCES="llr/simio.s llr/vgi.s llr/irq.s llr/textmode.s"
QSYS_SOURCES="main.s"

echo "Welcome to the QBuild: the QSys build script"

runcmd() {
  echo ">>> $1"
  eval "$1"
}

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <build|clean|sim|simtrace|simdebug> [debug]"
  exit 1
fi

if [ "$2" = "debug" ]; then
  set -x
fi

if [ "$1" = "clean" ]; then
  rm -f ${BUILD_FOLDER}/*.qo ${BUILD_FOLDER}/*.map ${BUILD_FOLDER}/*.bin ${BUILD_FOLDER}/*.gray ${BUILD_FOLDER}/qasflags ${BUILD_FOLDER}/*.log
  echo "Done removing output files from build folder."
  exit 0
fi

PYTHON_CANDIDATES=("../qas/.venv/bin/python" "/opt/homebrew/bin/python3" $(which python3) $(which foo))
for candidate in "${PYTHON_CANDIDATES[@]}"; do
  echo "Looking for Python interpreter at ${candidate}..."
  if [ -f $candidate ]; then
    PYTHON=${candidate}
    break
  fi
done

if [ -z ${PYTHON+x} ]; then
  echo "Unable to locate the Python interpreter. Aborting"
  exit 1
else 
  echo "Found Python interpreter at ${PYTHON}"
fi

if [ "$1" = "build" ]; then
  if [ ! -f ${BUILD_FOLDER}/qasflags ]; then
    echo "Building the memory map (as QAS flags) from QSim configuration: ${QSIM_CONFIG}..."
    runcmd "${PYTHON} tools/cfg2make.py ${QSIM_CONFIG} > ${BUILD_FOLDER}/qasflags"
  else
    echo "Memory map is already built, skipping..."
  fi

  if [ ! -f ${BUILD_FOLDER}/bitfont.gray ]; then
    echo "Building the LLR bitmap font from TTF font file: ${LLR_FONT}..."
    runcmd "tools/bitfont/mkfont.sh ${LLR_FONT} ${BUILD_FOLDER}/bitfont.gray"
    echo
  else
    echo "LLR bitmap font is already built, skipping..."
  fi

  echo "Building the main LLR system..."
  QASFLAGS="$(cat ${BUILD_FOLDER}/qasflags)"
  runcmd "${PYTHON} ${QAS} ${QASFLAGS} -m ${BUILD_FOLDER}/qsys.map -o ${BUILD_FOLDER}/qsys.bin ${QSYS_SOURCES} ${LLR_SOURCES}"
  qas_code=$?
  echo "All done!"
  exit $qas_code
fi

if [ ! -f ${BUILD_FOLDER}/qsys.bin ]; then
    echo "QSys binary is missing, build the system first: 'qbuild.sh build'!"
    exit 1
  else
    echo "Launching the QSim..."
fi

if [ "$1" = "sim" ]; then
    runcmd "${PYTHON} ${QSIM} -c ${QSIM_CONFIG} ${BUILD_FOLDER}/qsys.bin"
    exit $?
fi

if [ "$1" = "simtrace" ]; then
    echo "Simulator trace log will be saved as ${BUILD_FOLDER}/trace.log"
    runcmd "${PYTHON} ${QSIM} -t -c ${QSIM_CONFIG} ${BUILD_FOLDER}/qsys.bin" | tee ${BUILD_FOLDER}/trace.log
    exit $?
fi

if [ "$1" = "simdebug" ]; then
    runcmd "${PYTHON} ${QSIM} -d -c ${QSIM_CONFIG} ${BUILD_FOLDER}/qsys.bin"
    exit $?
fi

if [ "$2" = "debug" ]; then
  set +x
fi
