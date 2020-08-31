#!/usr/bin/env bash

# Define colors
RESTORE='\033[0m'
RED='\033[00;31m'
GREEN='\033[00;32m'
YELLOW='\033[00;33m'
BLUE='\033[00;34m'
CYAN='\033[00;36m'

# Intro to bootstrapper
echo "  _____ _             _    _____              "
echo " / ____| |           | |  |  __ \             "
echo "| (___ | |_ ___   ___| | _| |  | | ___   __ _ "
echo " \___ \| __/ _ \ / __| |/ / |  | |/ _ \ / _| |"
echo " ____) | || (_) | (__|   <| |__| | (_) | (_| |"
echo "|_____/ \__\___/ \___|_|\_\_____/ \___/ \__, |"
echo "                                         __/ |"
echo "                                        |___/" 
echo "Bootstrapper for local development environment"

# Move to the root directory
START_DIR="$(pwd)"
REPOSITORY_ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPOSITORY_ROOT_DIR" ]; then
   echo "Cannot determine StockDog root directory. Please run this script from within the repository."
   exit 1
fi
cd "$REPOSITORY_ROOT_DIR"
SCRIPTS_MODULE_DIR="${REPOSITORY_ROOT_DIR}/Scripts"

# Setup the logging file
LOG_FILE="${START_DIR}/bootstrap.log"
echo "" > "$LOG_FILE"
echo -e "Subcommand output is logged to ${YELLOW}${LOG_FILE}${RESTORE}\n"

###############################################################################
check_installed() {
   echo "   checking $1..."
   if ! hash $1 1>/dev/null 2>&1; then
      echo -e "${RED}$1 is not installed! ${RESTORE}"
      exit 1
   fi
}

# Check for prerequisites
echo -e "${CYAN}Checking for prerequisites${RESTORE}"
check_installed npm
check_installed mysql
check_installed python3
check_installed pip3
echo -e "${GREEN}All prerequisites detected!${RESTORE}"
echo ""

###############################################################################

echo -e "${CYAN}Setting up modules${RESTORE}"

###############################################################################
# Set up the web module
WEB_MODULE_DIR="${REPOSITORY_ROOT_DIR}/Web/stockdogweb"
echo -e "${BLUE}Setting up web (${WEB_MODULE_DIR})${RESTORE}"
cd "$WEB_MODULE_DIR"
echo "Installing npm dependencies"
if ! npm install 1>>"$LOG_FILE" 2>&1; then
   echo -e "${RED}Failed to install npm dependencies for web module${RESTORE}"; exit 1
fi
echo -e "${GREEN}Successfully set up web module${RESTORE}\n"
cd ../..

###############################################################################
# Set up the mobile module
MOBILE_MODULE_DIR="${REPOSITORY_ROOT_DIR}/Mobile/stockdogmobile"
echo -e "${BLUE}Setting up mobile (${MOBILE_MODULE_DIR})${RESTORE}"
cd "$MOBILE_MODULE_DIR"
echo "Installing npm dependencies"
if ! npm install 1>>"$LOG_FILE" 2>&1; then
   echo -e "${RED}Failed to install npm dependencies for mobile module${RESTORE}"; exit 1
fi
echo -e "${GREEN}Succesffully set up mobile module${RESTORE}\n"
cd ../..

###############################################################################
# Setup the service module
SERVICE_MODULE_DIR="${REPOSITORY_ROOT_DIR}/Service"
echo -e "${BLUE}Setting up the service (${REPOSITORY_ROOT_DIR})${RESTORE}"
cd "$REPOSITORY_ROOT_DIR"
echo "Installing python3 dependencies"
if ! pip3 install -r requirements.txt --user 1>>"$LOG_FILE" 2>&1; then
   echo -e "${RED}Failed to install python3 dependencies for service module${RESTORE}"; exit 1
fi
echo -e "${GREEN}Successfully setup service module${RESTORE}\n"

###############################################################################
# Setup the StockDog database
echo "Creating the StockDog database"
cd "$SERVICE_MODULE_DIR"
init_sql="${SERVICE_MODULE_DIR}/db/init.sql"
echo "${YELLOW}${LOG_FILE}${RESTORE}"
if ! mysql < $init_sql 1>>"$LOG_FILE" 2>&1; then
   echo -e "${RED}Failed to bootstrap the StockDog database"
   echo -e "Make sure MySQL server is running and ~/.my.cnf is set up correctly.${RESTORE}"
   exit 1
fi

echo -e "${GREEN}Successfully set up StockDog database${RESTORE}\n"
cd ..

###############################################################################
# Close bootstrapper
echo -e "Bootstrapping complete!"
echo -e "For more info, check the log file: ${YELLOW}${LOG_FILE}${RESTORE}"














