# MacroTools.py
# v1.0
#
# Record, playback and save actions performed in Maya as macros.
# Includes basic text editing capabilities.
#
# Brooke Waddington
# https://github.com/BrookeWaddington/MacroTools
#
# Based on the Brave Rabbit tool Actor Tools by Ingo Clemens.

# TODO: FEATURE LIST
#       - [Bug] canceling creating a macro from the dialog causes a nonetype error
#       - [DONE] clear a macro contents without re-recording
#       - [DONE] append recording from any line "start new recording at line X"
#       - [DONE] make Run Macro work
#       - [DONE] give placeholder edit/save/cancel buttons real functionality
#       - [DONE] debug the console output options, they don't seem to be working
#       - [DONE] make recording state clearer with red background on record button
#       - [DONE] error when trying to record the same macro directly after recording
#       - [DONE] clear Macro button
#       - [DONE] rebuild how backups work with a more generic backup method
#       - [DONE] install PyQt4/5 and sip to change text color of record button (PySide2 instead)
#       - [DONE] clearer UI for text edit options and to differentiate from the script editor readout
#       - [DONE] copy to clipboard (button made)
#       - [DONE] grey out EDIT button when editing and save/cancel vice versa
#       - [DONE][Bug] clearing macro doesn't create proper Undo behaviour
#       - [DONE] if no macro is selected grey out and CLEAR the scrollfield
#       - [DONE] rename a macro
#       - [DONE] option menu: open destination folder for macros
#       - [DONE] option menu: change macro folder path with warning
#       - confirm before changing the active macro as all unsaved data will be lost
#       - option menu: prefix get/set
#       - [BackLog] icons for stop/record/play/delete/edit/clear
#       - [BackLog] macro button grid for browsing macros to use
#       - [BackLog] bind keys to macros ie "press shift + 6 and macro6 runs"

# PySide2 custom UI example
# https://luckcri.blogspot.com/2018/04/pyside2-ui-example-for-maya.html

import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as omUI
import maya.cmds as cmds
import maya.mel as mel

from functools import partial
from PySide2 import QtWidgets, QtGui, QtCore
from shiboken2 import wrapInstance
import os, sys, subprocess


class MacroTools:

    def __init__(self):
        self.version = '0.01 beta'
        self.creator = 'Brooke Waddington'
        self.copyright = 'Brooke Waddington'
        self.windowName = 'MacroTools'
        self.macroFolderPath = 'null'  # Using a null arg with os.path.exists causes an error
        self.macroPrefix = ''  # No prefix
        self.recording = False

        # Rename UI
        self.renameWindow = ''
        self.renameNameField = ''
        self.renameFinishButton = ''
        self.renameIncludePrefix = ''

        # Main UI
        self.window = 'MacroToolsWindow'
        self.createMacroButton = ''
        self.debugButton = ''
        self.recordStartButton = ''
        self.recordStopButton = ''
        self.playMacroButton = ''
        self.clearMacroButton = ''
        self.deleteMacroButton = ''
        self.macroEditButton = ''
        self.macroSaveEditButton = ''
        self.macroUndoEditButton = ''
        self.macroRedoEditButton = ''
        self.macroCancelEditButton = ''
        self.macroCopyToClipboardButton = ''
        self.macroRenameButton = ''

        self.macroFileField = ''

        self.macroScrollField = ''
        self.scrollFieldDefaultBGColor = (0.1686, 0.1686, 0.1686)  # Default gray
        self.scrollFieldActiveBGColor = (0.1, 0.1, 0.1)  # Dark gray
        self.scrollFieldIDisabledBGColor = (0.225, 0.225, 0.225)  # Medium gray

        # TODO: Guessed the gray value for buttons, cant seem to query it. Find the exact value
        self.buttonDefaultColor = (0.38, 0.38, 0.38)  # Medium gray
        self.toggleColor = False
        self.recordingOnStyleSheet = (
                "QPushButton:disabled {"
                    "color: white;"
                    "background-color: rgb(150, 10, 10) }")
        self.recordingOffStyleSheet = (
                "QPushButton:disabled {"
                    "background-color: rgb(75, 75, 75) }"
                "QPushButton {"
                    "background-color: rgb(90, 90, 90);"
                "QPushButton:hover {"
                    "background-color: rgb(90, 90, 90) }")

        # TODO: Organize these variables to be clearer
        self.activeMacro = ''
        self.activeMacroPath = ''

        self.newMacroFile = ''
        self.newMacroPath = ''

        self.macroOption = ''
        self.openMacroFile = ''

        self.activeMacroBackUps = []
        self.backUpsIndex = 1

        # Script Editor Output Settings
        self.old_echoAllLines = ''
        self.old_showLineNumbersIsOn = ''
        self.old_stackTraceIsOn = ''
        self.suppressErrors = ''
        self.suppressInfo = ''
        self.suppressResults = ''
        self.suppressStackWindow = ''
        self.suppressWarnings = ''

        # #Example Style Sheet
        # self.stylesheet = (
        #     "QPushButton {"
        #         "color: red;"
        #         "background-color: green;"
        #         "border-style: outset;"
        #         "border-width: 2px;"
        #         "border-radius: 5px;"
        #         "border-color: beige;"
        #         "font: bold 14px;"
        #         "min-width: 10em;"
        #         "padding: 6px }"
        #     "QPushButton:hover {"
        #         "color: green;"
        #         "background-color: blue }"
        #     "QPushButton:pressed {"
        #         "color: blue;"
        #         "background-color: red }")
        self._checkMacroFolderPath()
        self._buildUI()

    def _buildUI(self):
        """
        Create the macro tool window
        """
        # Window Settings
        # If the window already exists delete the existing UI before drawing it again
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window)

        # Set the window size
        if cmds.windowPref(self.window, exists=True):
            cmds.windowPref(self.window, e=True, w=600, h=288)

        cmds.window(self.window, t=self.windowName, w=600, h=288, mb=True)
        layout = cmds.formLayout(p=self.window)

        cmds.menu(l='Options')
        cmds.menuItem(l='Open Macro Folder Path', c=partial(self._openMacroFolderPath))
        cmds.menuItem(l='Change Macro Folder Path', c=partial(self._changeMacroFolderPath, True))

        # Commented out until the rest of the prefix functionality is built
        #cmds.menuItem(l='Update Macro Prefix')#, c=partial(self._openAbout))

        # Left Column UI Holds the Debug Button, Create Macro frameLayout, and Active Macro frameLayout
        leftColumn = cmds.columnLayout(adjustableColumn=True, p=layout, w=300, h=190)
        cmds.formLayout(layout, e=True, af=(leftColumn, 'top', 5))
        cmds.formLayout(layout, e=True, af=(leftColumn, 'left', 5))

        # Debug Button
        self.debugButton = cmds.button(l='Debug Button', w=50, command=self._debugButton)

        # Frame Layout Create Macros
        cmds.frameLayout(l='Create Macro', marginWidth=10, marginHeight=10, collapsable=True)
        self.macroFileField = cmds.textFieldButtonGrp(
            l='Macro File' + self.macroPrefix,
            buttonLabel='...',
            cw3=(60, 160, 30),
            co3=(0, 5, 0),
            ct3=('both', 'both', 'both'),
            bc=partial(self._openFileList))
        self.createMacroButton = cmds.button(l='Create New Macro', w=50, command=self._checkCreateMacro)
        cmds.separator(h=5, style='none')
        cmds.setParent('..')

        # Frame Layout Active Macro
        cmds.frameLayout(l='Active Macro', marginWidth=10, marginHeight=10)
        self.macroOption = cmds.optionMenu(cc=partial(self._loadMacroButton))
        cmds.setParent('..')
        cmds.setParent('..')  # Close the leftColumn

        # Stop Recording Button
        self.recordStopButton = cmds.button(l='Stop', w=88, h=30, en=False, command=partial(self._recording, False))
        cmds.formLayout(layout, e=True, af=(self.recordStopButton, 'left', 20))
        cmds.formLayout(layout, e=True, aoc=(self.recordStopButton, 'bottom', -40, leftColumn))

        # Record Button
        self.recordStartButton = cmds.button(l='Record', w=88, h=30, command=partial(self._recording, True))
        cmds.formLayout(layout, e=True, ac=(self.recordStartButton, 'left', 5, self.recordStopButton))
        cmds.formLayout(layout, e=True, aoc=(self.recordStartButton, 'top', 0, self.recordStopButton))

        # Play Button
        self.playMacroButton = cmds.button(l='Play', w=88, h=30, command=self._runMacroButton)
        cmds.formLayout(layout, e=True, ac=(self.playMacroButton, 'left', 5, self.recordStartButton))
        cmds.formLayout(layout, e=True, aoc=(self.playMacroButton, 'top', 0, self.recordStopButton))

        # Delete Button
        self.deleteMacroButton = cmds.button(l='Delete', w=88, h=30, command=self._deleteMacroButton)
        cmds.formLayout(layout, e=True, af=(self.deleteMacroButton, 'left', 20))
        cmds.formLayout(layout, e=True, aoc=(self.deleteMacroButton, 'bottom', -40, self.recordStopButton))

        # Quick Edit Button
        self.macroRenameButton = cmds.button(l='Rename', w=88, h=30, command=self._openRenameWindow)
        cmds.formLayout(layout, e=True, ac=(self.macroRenameButton, 'left', 5, self.deleteMacroButton))
        cmds.formLayout(layout, e=True, aoc=(self.macroRenameButton, 'top', 0, self.deleteMacroButton))

        # Clear Button
        self.clearMacroButton = cmds.button(l='Clear', w=88, h=30, command=self._clearMacroButton)
        cmds.formLayout(layout, e=True, ac=(self.clearMacroButton, 'left', 5, self.macroRenameButton))
        cmds.formLayout(layout, e=True, aoc=(self.clearMacroButton, 'top', 0, self.deleteMacroButton))

        # Right Side Scroll Field
        self.macroScrollField = cmds.scrollField(
            editable=False,
            backgroundColor=self.scrollFieldIDisabledBGColor,
            wordWrap=False,
            p=layout)

        cmds.formLayout(layout, e=True, aoc=(self.macroScrollField, 'top', 0, leftColumn))
        cmds.formLayout(layout, e=True, ac=(self.macroScrollField, 'left', 5, leftColumn))
        cmds.formLayout(layout, e=True, af=(self.macroScrollField, 'bottom', 40))
        cmds.formLayout(layout, e=True, af=(self.macroScrollField, 'right', 5))

        # Copy to Clipboard
        self.macroCopyToClipboardButton = cmds.button(l='Copy', p=layout, w=40, command=self._copyToClipboardButton)
        cmds.formLayout(layout, e=True, af=(self.macroCopyToClipboardButton, 'top', 10))
        cmds.formLayout(layout, e=True, af=(self.macroCopyToClipboardButton, 'right', 20))

        # Edit Button
        self.macroEditButton = cmds.button(l='Edit', p=layout, w=40, command=self._editButton)
        cmds.formLayout(layout, e=True, aoc=(self.macroEditButton, 'bottom', -30, self.macroScrollField))
        cmds.formLayout(layout, e=True, ac=(self.macroEditButton, 'left', 5, leftColumn))

        # Save Button
        self.macroSaveEditButton = cmds.button(l='Save', en=False, p=layout, w=40, command=self._saveButton)
        cmds.formLayout(layout, e=True, aoc=(self.macroSaveEditButton, 'top', 0, self.macroEditButton))
        cmds.formLayout(layout, e=True, ac=(self.macroSaveEditButton, 'left', 5, self.macroEditButton))

        # Undo Button
        self.macroUndoEditButton = cmds.button(l='Undo', p=layout, w=40, command=self._undoButton)
        cmds.formLayout(layout, e=True, aoc=(self.macroUndoEditButton, 'top', 0, self.macroEditButton))
        cmds.formLayout(layout, e=True, ac=(self.macroUndoEditButton, 'left', 5, self.macroSaveEditButton))

        # Redo Button
        self.macroRedoEditButton = cmds.button(l='Redo', p=layout, w=40, command=self._redoButton)
        cmds.formLayout(layout, e=True, aoc=(self.macroRedoEditButton, 'top', 0, self.macroEditButton))
        cmds.formLayout(layout, e=True, ac=(self.macroRedoEditButton, 'left', 5, self.macroUndoEditButton))

        # Cancel Button
        self.macroCancelEditButton = cmds.button(l='Cancel', en=False, p=layout, w=40, command=self._cancelButton)
        cmds.formLayout(layout, e=True, aoc=(self.macroCancelEditButton, 'bottom', -30, self.macroScrollField))
        cmds.formLayout(layout, e=True, af=(self.macroCancelEditButton, 'right', 5))

        # Refresh the macro list
        self._listMacros()
        self._loadMacroButton()

        cmds.showWindow(self.window)

    def _debugButton(self, *args):
        """
        Debugging button, handy for testing.
        """
        directory = cmds.optionVar(q='MacroToolsDirectory')
        print(directory)

    def _openMacroFolderPath(self, *args):
        """
        Try to open the specific file path
        """
        # Windows
        if sys.platform == 'win32':
            try:
                os.startfile(self.macroFolderPath)
            except OSError:
                OpenMaya.MGlobal_displayError('File directory not found.')
        # MacOS
        else:
            try:
                subprocess.call([open, self.macroFolderPath])
            except OSError:
                OpenMaya.MGlobal_displayError('File directory not found.')

    def _checkMacroFolderPath(self, *args):
        """
        Check if a directory path exists. Prompt the user to point to it if it does not.
        """
        title = 'Macro Directory Missing'
        message = 'Please select a location for Macros to be stored.'
        icon = 'warning'

        self.macroFolderPath = cmds.optionVar(q='MacroToolsDirectory')

        # If the folder path preferences are null ask user to change it
        if not self.macroFolderPath:
            if self._dialogBool(title, message, icon):
                self._changeMacroFolderPath(refresh=False)

        # If the folder path can not be found ask the user to change it
        elif not os.path.exists(self.macroFolderPath):
            if self._dialogBool(title, message, icon):
                self._changeMacroFolderPath(refresh=False)

    def _changeMacroFolderPath(self, refresh=True, *args):
        """
        Change the macro folder path and save to preferences
        """
        newDirectory = cmds.fileDialog2(
            fileMode=3,
            okCaption='OK',
            caption='Select or Create Macro Folder Path')

        if newDirectory:
            self.macroFolderPath = newDirectory[0]

        cmds.optionVar(sv=('MacroToolsDirectory', self.macroFolderPath))

        if refresh:
            self._listMacros()

    def _openRenameWindow(self, *args):
        """
        Opens the window for renaming the active macro.
        """
        # Disable the main UI while renaming
        #self._toggleActiveUI(enable=False)

        if cmds.window(self.renameWindow, exists=True):
            cmds.deleteUI(self.renameWindow)
        # Set the window size
        if cmds.windowPref(self.renameWindow, exists=True):
            cmds.windowPref(self.renameWindow, e=True, w=300, h=75)

        if cmds.optionVar(ex='macroToolsRenameIncludePrefix'):
            includePrefixCheck = cmds.optionVar(q='macroToolRenameIncludePrefix')

        # get the user preferences
        includePrefixCheck = False

        # Create the Window and UI
        self.renameWindow = cmds.window(title="Rename Macro", widthHeight=(300, 75))
        cmds.columnLayout(adj=True, rowSpacing=5, w=300, h=75)
        self.renameNameField = cmds.textFieldGrp(
            l='New Name',
            cw2=(100, 160),
            co2=(0, 5),
            ct2=('both', 'both'),
            tx=self.activeMacro)
        # Commented out prefix option until it is properly added in
        # self.renameIncludePrefix = cmds.checkBoxGrp(
        #     l='Include prefix',
        #     v1=includePrefixCheck,
        #     cw2=(106, 30),
        #     co2=(5, 0),
        #     ct2=('right', 'both'))
        cmds.button(self.renameFinishButton, l='Rename', command=self._macroRenameButton)
        cmds.setParent('..')

        cmds.showWindow(self.renameWindow)

    def _macroRenameButton(self, *args):
        """
        Rename the active macro.
        """
        # Save old name and create new name
        newName = cmds.textFieldGrp(self.renameNameField, q=True, tx=True)
        if self.renameIncludePrefix:
            newName = self.macroPrefix + newName

        oldPath = self.activeMacroPath
        self.activeMacroPath = self.activeMacroPath.rsplit('/', 1)[0] + '/' + newName + '.txt'

        # Rename the macro file
        try:
            os.rename(oldPath, self.activeMacroPath)
        except OSError:
            OpenMaya.MGlobal_displayError('File name is already taken.')
            self.activeMacroPath = oldPath
            return

        # Refresh macro list
        self._listMacros()
        cmds.optionMenu(self.macroOption, e=True, v=newName)
        #self._loadMacroButton()

        # Set the preferences
        cmds.optionVar(iv=('macroToolRenameIncludePrefix', cmds.checkBoxGrp(self.renameIncludePrefix, q=True, v1=True)))

        # Close the rename window
        cmds.deleteUI(self.renameWindow)

    def _copyToClipboardButton(self, *args):
        """
        Copy the text in the macro scroll field to the the clipboard.
        """
        textToClipBoard = cmds.scrollField(self.macroScrollField, q=True, text=True)
        QtWidgets.QApplication.clipboard().setText(textToClipBoard)

    def _undoButton(self, *args):
        """
        Save the last string in the list of backups to the active macro, decrementing.
        """
        self._updateUndoRedoButtonStates()

        try:
            self.backUpsIndex -= 1
            newText = self.activeMacroBackUps[self.backUpsIndex - 1]
            self._clamp(self.backUpsIndex, 0, len(self.activeMacroBackUps) - 1)
            self._updateUndoRedoButtonStates()
            self._saveStringToMacro(newText)
        except IndexError:
            print('index error')
            return

    def _redoButton(self, *args):
        """
        Save the next string in the list of backups to the active macro, incrementing.
        """
        self._updateUndoRedoButtonStates()

        try:
            self.backUpsIndex += 1
            newText = self.activeMacroBackUps[self.backUpsIndex - 1]
            self._clamp(self.backUpsIndex, 0, len(self.activeMacroBackUps))
            self._updateUndoRedoButtonStates()
            self._saveStringToMacro(newText)
        except IndexError:
            print('index error')
            return

    def _updateUndoRedoButtonStates(self, *args):
        """
        Disable or enable the redo and undo buttons depending on the current backup index.
        """
        index = self.backUpsIndex
        length = len(self.activeMacroBackUps)

        # Disable Undo
        if index <= 1:
            cmds.button(self.macroUndoEditButton, e=True, enable=False)
        # Enable Undo
        else:
            cmds.button(self.macroUndoEditButton, e=True, enable=True)

        # Disable Redo
        if index >= length:
            cmds.button(self.macroRedoEditButton, e=True, enable=False)
        # Enable Redo
        else:
            cmds.button(self.macroRedoEditButton, e=True, enable=True)

    def _editButton(self, *args):
        """
        Enable editing of the scroll field window and toggle editing UI elements on/off.
        """
        # Enable Editing
        cmds.scrollField(self.macroScrollField, e=True, editable=True, backgroundColor=self.scrollFieldActiveBGColor)

        # Toggle UI for editing
        cmds.button(self.macroEditButton, e=True, en=False)
        cmds.button(self.macroSaveEditButton, e=True, en=True)
        cmds.button(self.macroCancelEditButton, e=True, en=True)
        self._toggleActiveUI(enable=False, includeStopButton=False, includeCreateUI=True)

    def _saveButton(self, *args):
        """
        Save the current scrollField text to the active macro and toggle editing UI elements on/off.
        """
        self._addActiveMacroBackUp()
        newText = cmds.scrollField(self.macroScrollField, q=True, text=True)

        cmds.button(self.macroEditButton, e=True, en=True)
        cmds.button(self.macroSaveEditButton, e=True, en=False)
        cmds.button(self.macroCancelEditButton, e=True, en=False)
        self._toggleActiveUI(enable=True, includeStopButton=False, includeCreateUI=True)

        self._saveStringToMacro(newText)
        self._addActiveMacroBackUp()

    def _cancelButton(self, *args):
        """
        Reset the scroll field and toggle editing UI elements on/off.
        """
        # Toggle UI for editing
        cmds.button(self.macroEditButton, e=True, en=True)
        cmds.button(self.macroSaveEditButton, e=True, en=False)
        cmds.button(self.macroCancelEditButton, e=True, en=False)
        self._toggleActiveUI(enable=True, includeStopButton=False, includeCreateUI=True)

        # Reset the scroll field
        self._resetMacroScrollField()

    def _saveStringToMacro(self, newText='', *args):
        """
        Save edits in the scrollField to the active macro.
        If undo is true, save the backup to the active macro.
        :param newText: The content to be saved to the macro. default is empty.
        """
        # Write to file
        with open(self.activeMacroPath, 'w') as openMacroFile:
            openMacroFile.write(newText)

        # with open(self.activeMacroPath) as openMacroFile:
        #     print(openMacroFile.read())

        # Update the scroll field to reflect the changes
        self._resetMacroScrollField()

    def _checkCreateMacro(self, *args):
        """
        Create a new blank macro from the macroFileField
        """
        # Dialog Message Contents
        title = 'Create Macro'
        message = ' already exists. Do you want to replace it?'  # Macro name is added to message
        icon = 'question'

        # If the new macro name is already taken ask the user to overwrite
        newMacroName = cmds.textFieldButtonGrp(self.macroFileField, q=True, tx=True)
        if newMacroName:
            for macro in self._getMacros():
                # Check if new macro name is taken
                macroName = macro.split('.txt')[0]
                if macroName == newMacroName and self._dialogBool(title, macro + message, icon) is True:
                    # Overwrite the macro and return
                    self._createMacro(newMacroName)
                    return
            # Name is not taken, create the macro
            self._createMacro(newMacroName)
        else:
            OpenMaya.MGlobal_displayError('No new macro file is defined')

    def _createMacro(self, newMacroName):
        """
        Creates a text file and reloads the macro list
        with the new macro as the active macro
        :param newMacroName: The name of the new macro
        """
        # Create Macro
        self.newMacroPath = self.macroFolderPath + '/' + self.macroPrefix + newMacroName + '.txt'
        self.newMacroFile = open(self.newMacroPath, 'w')
        self.newMacroFile.close()

        # Refresh the macro list with the new macro as the active macro
        self._listMacros()
        cmds.optionMenu(self.macroOption, e=True, v=newMacroName)
        self._loadMacroButton()

    def _deleteMacroButton(self, *args):
        """
        Delete the active macro
        """
        if self.activeMacro:
            confirm = cmds.confirmDialog(
                title='Delete Macro',
                message='Delete the macro \"' + self.activeMacro + '\"?',
                button=['Delete', 'Cancel'],
                defaultButton='Delete',
                cancelButton='Cancel',
                dismissString='Cancel',
                icon='warning')
        else:
            OpenMaya.MGlobal_displayError('No macro file is defined')
            return

        if confirm == 'Delete':
            # Delete the active file
            os.remove(self.activeMacroPath)

            # Refresh the macro list
            self._listMacros()
            self._loadMacroButton()
        elif confirm == 'Cancel':
            return

    def _openFileList(self, *args):
        """
        Open a file dialog for letting the user choose a file for saving the macro
        """
        # Open the dialog
        fileName = cmds.fileDialog2(
            dir=self.macroFolderPath,
            fileMode=0,
            fileFilter='Text Files (*.txt)',
            okCaption='OK',
            caption='Select or Create a %s File' % 'New Macro')
        if not fileName:
            return

        # Add prefix to file name
        prefixAdded = fileName[0].replace(os.path.basename(fileName[0]),
                                          self.macroPrefix + os.path.basename(fileName[0]))
        self.newMacroPath = prefixAdded
        print(self.newMacroPath)

        # Return before updating the macro file field
        if not self.newMacroPath:
            return

        # Update field with new macro name
        cmds.textFieldButtonGrp(self.macroFileField, e=True, text=os.path.basename(self.newMacroPath).split('.')[0])

    # def _checkRecordingStart(self, *args):
    #     """
    #     Check the active macro before recording,
    #     ask for user input if the file is not empty
    #     """
    #     with open(self.activeMacroPath) as self.openMacroFile:
    #         if self.openMacroFile.read():
    #             self._recording(True)
    #         # The active file is empty, start recording
    #         else:
    #             self._recording(True)
    #             return

    def _recording(self, recording, *args):
        """
        Record the script editor output to the active macro or
        Stop recording the script editor output to the active macro
        """
        # Create a backup before writing to the text file or stopping the recording
        self._addActiveMacroBackUp()

        # Check for an active recording before starting a new one
        if recording is True:
            if self.recording is True:
                OpenMaya.MGlobal_displayError('A recording is already in progress')
                return
            self.recording = True

            # Set the console settings before recording
            self._saveConsoleSettings()
            self._setConsoleRecordingSettings()

            # Set recording UI state
            self._toggleActiveUI(enable=False)
            cmds.button(self.recordStopButton, e=True, en=True)
            recordButton = wrapInstance(long(omUI.MQtUtil.findControl(self.recordStartButton)), QtWidgets.QPushButton)
            recordButton.setStyleSheet(self.recordingOnStyleSheet)

            # Set the active macro to the console readout file
            cmds.scriptEditorInfo(historyFilename=self.activeMacroPath)
            print('recording started...')
            cmds.scriptEditorInfo(writeHistory=True)

        # Stop recording
        elif recording is False:
            if self.recording is False:
                return
            self.recording = False

            # Stop recording
            cmds.scriptEditorInfo(writeHistory=False)
            self._resetConsoleSettings()

            # Enable UI
            self._toggleActiveUI(enable=True, includeStopButton=False)
            recordButton = wrapInstance(long(omUI.MQtUtil.findControl(self.recordStartButton)), QtWidgets.QPushButton)
            recordButton.setStyleSheet(self.recordingOffStyleSheet)
            cmds.button(self.recordStopButton, e=True, en=False)

            # Review the recording in the scroll field
            self._resetMacroScrollField()

            print('recording stopped')

    def _toggleActiveUI(self, enable, includeCreateUI=True, includeStopButton=True):
        """
        Toggle the UI off/on, allow finer control over the create macro UI
        And for the stop button
        """
        # UI for creating a new macro
        if includeCreateUI:
            cmds.button(self.createMacroButton, e=True, en=enable)
            cmds.textFieldButtonGrp(self.macroFileField, e=True, en=enable)
            cmds.optionMenu(self.macroOption, e=True, en=enable)

        # Stop Button
        if includeStopButton:
            cmds.button(self.recordStopButton, e=True, en=enable)

        # UI that requires an active macro
        cmds.button(self.recordStartButton, e=True, en=enable)
        cmds.button(self.playMacroButton, e=True, en=enable)
        cmds.button(self.clearMacroButton, e=True, en=enable)
        cmds.button(self.deleteMacroButton, e=True, en=enable)
        cmds.button(self.macroEditButton, e=True, en=enable)
        cmds.button(self.macroUndoEditButton, e=True, en=enable)
        cmds.button(self.macroRedoEditButton, e=True, en=enable)
        # cmds.button(self.macroSaveEditButton, e=True, en=enable)
        # cmds.button(self.macroCancelEditButton, e=True, en=enable)
        cmds.button(self.macroCopyToClipboardButton, e=True, en=enable)
        cmds.button(self.macroRenameButton, e=True, en=enable)

    def _runMacroButton(self, *args):
        """        # cmds.textField(self.renameNameField)
        # cmds.button(self.renameFinishButton, l='Rename')rename
        Playback the active macro
        """
        print('playing back last recording...' + '\n')
        mel.eval('source \"' + self.activeMacroPath + '\";')
        print('playback finished.')

    def _clearMacroButton(self, *args):
        """
        Clears the contents from the active macro
        """
        # Add backup before clearing
        self._addActiveMacroBackUp()

        # Clear the active macro after confirming with the user
        with open(self.activeMacroPath) as openMacroFile:
            if openMacroFile.read():
                open(self.activeMacroPath, 'w').close()
                self._resetMacroScrollField()

        # Add backup after clearing
        self._addActiveMacroBackUp()

    def _getMacros(self, *args):
        """
        Return a list of macros based on the active folder
        """
        macros = []

        if os.path.exists(self.macroFolderPath):
            items = os.listdir(self.macroFolderPath)
            for i in items:
                # Only collect items which are text files and have the macro prefix
                if os.path.isfile(self.macroFolderPath + '/' + i):
                    if i.startswith(self.macroPrefix) and i.endswith('.txt'):
                        macros.append(i)

        return macros

    def _listMacros(self, *args):
        """
        Refresh the option menu to show all available macros.
        """
        # Clear the option menu before updating
        items = cmds.optionMenu(self.macroOption, q=True, ill=True)
        if items is not None:
            cmds.deleteUI(items)

        # Create a new list of macros with short names.
        macros = self._getMacros()
        if len(macros):
            cmds.menuItem('Select Macro', p=self.macroOption)
            for macro in macros:
                if self.macroPrefix:
                    trimmedMacroName = (macro.split(self.macroPrefix))[1].split(".txt")[0]
                else:
                    trimmedMacroName = macro.split(".txt")[0]
                cmds.menuItem(trimmedMacroName, p=self.macroOption)
        else:
            cmds.menuItem('No Macros', p=self.macroOption)

    def _loadMacroButton(self, *args):
        """
        Load the name of the selected macro then show the macro in the scroll field.
        Update the UI and save data after confirming with the user.
        """
        # By default assume the UI will be disabled
        enableUI = False

        if cmds.optionMenu(self.macroOption, q=True, sl=True) != 1:
            self.activeMacro = cmds.optionMenu(self.macroOption, q=True, v=True)
            self.activeMacroPath = self.macroFolderPath + '/' + self.macroPrefix + self.activeMacro + ".txt"
            self._resetMacroScrollField()

            # Clear any backups from previous active macro and add an initial backup
            del self.activeMacroBackUps[:]
            self.backUpsIndex = 0
            enableUI = True
        # Clear contents when no macro is selected
        elif cmds.optionMenu(self.macroOption, q=True, sl=True) == 1:
            cmds.scrollField(self.macroScrollField, e=True, editable=False, text='')
            del self.activeMacroBackUps[:]
            self.backUpsIndex = 0

        # Toggle the UI elements that require an active macro
        # Do not include the create macro UI elements
        self._toggleActiveUI(enableUI, includeCreateUI=False, includeStopButton=False)
        self._updateUndoRedoButtonStates()

        # Clear the active macro if no macro is selected from the list
        if not enableUI:
            self.activeMacro = ''

    def _addActiveMacroBackUp(self):
        """
        Add a new macro back up here, only add unique entries
        """
        with open(self.activeMacroPath) as openMacroFile:
            # Get the contents of the macro
            newBackUp = openMacroFile.read()

            # If there are already backups, check if the previous back
            # up is the same as the new one and add the new backup
            if len(self.activeMacroBackUps) != 0:
                previousBackUp = ''.join(map(str, self.activeMacroBackUps[-1:]))
                if previousBackUp != newBackUp and newBackUp is not False:
                    self.activeMacroBackUps.append(newBackUp)
                    self.backUpsIndex += 1
                    self._updateUndoRedoButtonStates()

            # If there are no other back ups and this one isn't empty add the new backup
            elif newBackUp is not False:
                self.activeMacroBackUps.append(newBackUp)
                self.backUpsIndex += 1
                self._updateUndoRedoButtonStates()

    def _resetMacroScrollField(self):
        """
        Load the active macro to the macroScrollField, disable
        the scroll field and create a backup of the macro
        """
        with open(self.activeMacroPath) as openMacroFile:
            macroText = openMacroFile.read()
            self.macroBackUp = macroText

            cmds.scrollField(
                self.macroScrollField,
                e=True,
                editable=False,
                backgroundColor=self.scrollFieldIDisabledBGColor,
                text=macroText)


    @staticmethod
    def _dialogBool(title, message, icon):
        """
        Return True/False after asking for user input, simplified for when Yes/No is sufficient
        """
        result = cmds.confirmDialog(
            title=title,
            message=message,
            button=['Yes', 'No'],
            defaultButton='Yes',
            cancelButton='No',
            dismissString='No',
            icon=icon)

        if result == 'Yes':
            return True
        else:
            return False

    def _setConsoleRecordingSettings(self):
        """
        Set the console output settings for best recording results
        """
        self.suppressErrors = cmds.scriptEditorInfo(e=True, suppressErrors=True)
        self.suppressInfo = cmds.scriptEditorInfo(e=True, suppressInfo=True)
        self.suppressResults = cmds.scriptEditorInfo(e=True, suppressResults=True)
        self.suppressStackWindow = cmds.scriptEditorInfo(e=True, suppressStackWindow=True)
        self.suppressWarnings = cmds.scriptEditorInfo(e=True, suppressWarnings=True)

        cmds.optionVar(iv=('echoAllLines', 0))
        cmds.optionVar(iv=('showLineNumbersIsOn', 0))
        cmds.optionVar(iv=('stackTraceIsOn', 0))

    def _resetConsoleSettings(self):
        """
        Set the console output settings to their original saved value
        """
        cmds.scriptEditorInfo(
            e=True,
            suppressErrors=self.suppressErrors,
            suppressInfo=self.suppressInfo,
            suppressResults=self.suppressResults,
            suppressStackWindow=self.suppressStackWindow,
            suppressWarnings=self.suppressWarnings)

        cmds.optionVar(iv=('echoAllLines', int(self.old_echoAllLines)))
        cmds.optionVar(iv=('showLineNumbersIsOn', self.old_showLineNumbersIsOn))
        cmds.optionVar(iv=('stackTraceIsOn', self.old_stackTraceIsOn))

    def _saveConsoleSettings(self):
        """
        Save the current settings of the console output
        """
        cmds.scriptEditorInfo(q=True, suppressErrors=True)
        cmds.scriptEditorInfo(q=True, suppressInfo=True)
        cmds.scriptEditorInfo(q=True, suppressResults=True)
        cmds.scriptEditorInfo(q=True, suppressStackWindow=True)
        cmds.scriptEditorInfo(q=True, suppressWarnings=True)

        self.old_echoAllLines = cmds.optionVar(q='echoAllLines')
        self.old_showLineNumbersIsOn = cmds.optionVar(q='showLineNumbersIsOn')
        self.old_stackTraceIsOn = cmds.optionVar(q='stackTraceIsOn')

    @staticmethod
    def _clamp(value, min, max):
        if value < min:
            return min
        elif value > max:
            return max
        else:
            return value