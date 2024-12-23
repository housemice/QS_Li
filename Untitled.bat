{\rtf1\ansi\ansicpg1252\cocoartf2820
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww29740\viewh18600\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 @echo off\
setlocal\
\
REM Function to check last operation's success or failure\
:checkError\
if %errorlevel% neq 0 (\
    echo Error occurred: %1\
    pause\
    exit /b 1\
) else (\
    echo %2\
)\
\
echo Starting script execution...\
\
REM Disable automatic timezone setting and set timezone to Baku\
echo Disabling automatic timezone setting...\
adb shell settings put global auto_time_zone 0\
call :checkError "Failed to disable automatic timezone." "Automatic timezone disabled successfully."\
\
echo Setting timezone to Baku...\
adb shell settings put global time_zone Asia/Baku\
call :checkError "Failed to set timezone to Baku." "Timezone set to Baku successfully."\
\
REM Uninstall all third-party apps\
echo Uninstalling all third-party apps...\
for /f "tokens=2 delims=:" %%i in ('adb shell pm list packages -3') do (\
    echo Uninstalling package %%i...\
    adb uninstall %%i\
    if %errorlevel% neq 0 (\
        echo Failed to uninstall package %%i\
    ) else (\
        echo Uninstalled %%i successfully.\
    )\
)\
\
echo All third-party apps uninstalled successfully.\
\
REM Install required apps\
echo Installing essential apps...\
adb install com.lixiang.chat.store.apk\
call :checkError "Failed to install Lixiang Chat Store." "Lixiang Chat Store installed successfully."\
\
adb install --user 0 Android_Settings.apk\
call :checkError "Failed to install Android Settings." "Android Settings installed successfully."\
\
adb install --user 0 Launcher.apk\
call :checkError "Failed to install Launcher." "Launcher installed successfully."\
\
adb install --user 0 Rear_App.apk\
call :checkError "Failed to install Rear App." "Rear App installed successfully."\
\
adb install --user 0 SMS_Messenger.apk\
call :checkError "Failed to install SMS Messenger." "SMS Messenger installed successfully."\
\
adb install --user 0 Waze.apk\
call :checkError "Failed to install Waze." "Waze installed successfully."\
\
adb install SwiftKey.apk\
call :checkError "Failed to install SwiftKey." "SwiftKey installed successfully."\
\
adb install YouTube_CarWizard.apk\
call :checkError "Failed to install YouTube CarWizard." "YouTube CarWizard installed successfully."\
\
echo Waiting for 2 seconds...\
timeout /t 2 /nobreak\
\
REM Set SwiftKey as the input method for multiple users\
echo Setting SwiftKey as input method for multiple users...\
adb shell ime enable --user 0 com.touchtype.swiftkey/com.touchtype.KeyboardService\
call :checkError "Failed to enable SwiftKey for user 0." "SwiftKey enabled for user 0."\
\
adb shell ime set --user 0 com.touchtype.swiftkey/com.touchtype.KeyboardService\
call :checkError "Failed to set SwiftKey as default for user 0." "SwiftKey set as default for user 0."\
\
adb shell ime enable --user 21473 com.touchtype.swiftkey/com.touchtype.KeyboardService\
call :checkError "Failed to enable SwiftKey for user 21473." "SwiftKey enabled for user 21473."\
\
adb shell ime set --user 21473 com.touchtype.swiftkey/com.touchtype.KeyboardService\
call :checkError "Failed to set SwiftKey as default for user 21473." "SwiftKey set as default for user 21473."\
\
adb shell ime enable --user 6174 com.touchtype.swiftkey/com.touchtype.KeyboardService\
call :checkError "Failed to enable SwiftKey for user 6174." "SwiftKey enabled for user 6174."\
\
adb shell ime set --user 6174 com.touchtype.swiftkey/com.touchtype.KeyboardService\
call :checkError "Failed to set SwiftKey as default for user 6174." "SwiftKey set as default for user 6174."\
\
echo Reinstalling Lixiang Chat Store...\
adb install com.lixiang.chat.store.apk\
call :checkError "Failed to reinstall Lixiang Chat Store." "Lixiang Chat Store reinstalled successfully."\
\
echo Waiting for 2 seconds...\
timeout /t 2 /nobreak\
\
REM Set install permissions for Lixiang Chat Store\
echo Setting install permissions for Lixiang Chat Store for multiple users...\
adb shell "for user in 0 6174 21473; do appops set --user %user% com.lixiang.chat.store REQUEST_INSTALL_PACKAGES allow; done"\
call :checkError "Failed to set install permissions for Lixiang Chat Store." "Install permissions for Lixiang Chat Store set successfully."\
\
echo Script execution completed.\
pause}