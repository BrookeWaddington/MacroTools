import os
from functools import partial
from PySide2 import QtWidgets
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import maya.mel as mel
from shiboken2 import wrapInstance

# TODO: FEATURE LIST
#       - add to shelf button
#       - delete line by line with buttons
#       - add nice number formatting on left side of scroll field
#       - bind keys to macros ie "press shift + 6 and macro6 runs"
#       - [MEDIUM] add warnings for editing/saving/cancelling
#       - figure out how to get maya console output without writing to a file
#       - live updating of scroll field text as output is recorded
#       - [DONE] clear a macro contents without re-recording
#       - [DONE] append recording from any line "start new recording at line X"
#       - [DONE] make Run Macro work
#       - [DONE] give placeholder edit/save/cancel buttons real functionality
#       - [DONE] debug the console output options, they don't seem to be working
#       - [DONE] make recording state clearer with red background on record button
#       - [DONE] error when trying to record the same macro directly after recording
#       - [DONE] clear Macro button
#       - [DONE] rebuild how backups work with a more generic backup method
#       - [DONE] install PyQt4 and sip to change text color of record button
#       - [LOW] move clear button to more logical "editing" part of UI
#       - clearer UI for text edit options and to differentiate from the script editor readout
#       - macro button grid for browsing macros to use
#       - rename a macro
#       - options menu with preferences?
#       - copy to clipboard (button made)
#       - quick edit mode

# PySide2 custom UI example
# https://luckcri.blogspot.com/2018/04/pyside2-ui-example-for-maya.html
#


class MacroTools:

    def __init__(self):
        self.version = '0.01 beta'
        self.creator = 'Brooke Waddington'
        self.copyright = 'Brooke Waddington'
        self.windowName = 'MacroTools'
        self.macroFolderPath = 'C:/Users/Brooke/Desktop/Macros'
        self.macroPrefix = ''  # No prefix
        self.recording = False

        # UI
        self.window = 'MacroToolsWindow'
        self.createMacroButton = ''
        self.debugButton = ''
        self.recordStartButton = ''
        self.recordStartButtonColor = (0.4, 0.1, 0.1)  # Dark red
        self.recordStopButton = ''
        self.runMacroButton = ''
        self.clearMacroButton = ''
        self.deleteMacroButton = ''
        self.macroEditButton = ''
        self.macroSaveEditButton = ''
        self.macroUndoEditButton = ''
        self.macroRedoEditButton = ''
        self.macroCancelEditButton = ''
        self.macroCopyToClipboardButton = ''
        self.macroQuickEditButton = ''

        self.macroFileField = ''

        self.macroScrollField = ''
        self.scrollFieldDefaultBGColor = (0.1686, 0.1686, 0.1686)  # Default gray
        self.scrollFieldActiveBGColor = (0.1, 0.1, 0.1)  # Dark gray
        self.scrollFieldIDisabledBGColor = (0.225, 0.225, 0.225)  # Medium gray

        # TODO: Guessed the gray value for buttons, cant seem to query it. Find the exact value
        self.buttonDefaultColor = (0.38, 0.38, 0.38)  # Medium gray
        self.toggleColor = False

        # TODO: Organize these variables to be clearer
        self.activeMacro = ''
        self.activeMacroPath = ''

        self.newMacroFile = ''
        self.newMacroPath = ''

        self.macrosFolderPath = ''
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
            cmds.windowPref(self.window, e=True, w=600, h=150)

        cmds.window(self.window, t=self.windowName, w=600, h=150, mb=True)
        layout = cmds.formLayout(p=self.window)

        # Left Column UI
        leftColumn = cmds.columnLayout(adjustableColumn=True, p=layout, w=300)

        # Debug Button
        self.debugButton = cmds.button(l='Debug Button', w=50, command=self._debugButton)
        debugButton = wrapInstance(long(OpenMayaUI.MQtUtil.findControl(self.debugButton)), QtWidgets.QPushButton)
        debugButton.setStyleSheet(
            "QPushButton {"
                "background-color: green;"
                "border-style: outset;"
                "border-width: 0px;"
                "border-radius: 5px;"
                "border-color: beige;"
                #"font: bold 14px;"
                "min-width: 10em;"
                "padding: 6px;}"
            "QPushButton:hover {"
                "background-color: blue}"
            "QPushButton:pressed {" 
                "background-color: red }")

        # Left Side Create Macros
        cmds.frameLayout(l='Create Macro', marginWidth=10, marginHeight=10)
        self.macroFileField = cmds.textFieldButtonGrp(l='Macro File' + self.macroPrefix,
                                                      buttonLabel='...',
                                                      cw3=(60, 160, 30),
                                                      co3=(0, 5, 0),
                                                      ct3=('both', 'both', 'both'),
                                                      bc=partial(self._openFileList))

        self.createMacroButton = cmds.button(l='Create New Macro', w=50, command=self._checkCreateMacro)
        cmds.separator(h=5, style='none')
        cmds.setParent('..')

        # Left Side Active Macro Options
        cmds.frameLayout(l='Active Macro Options', marginWidth=10, marginHeight=10)
        self.macroOption = cmds.optionMenu(cc=partial(self._loadMacroButton))
        cmds.separator(h=5, style='doubleDash')

        # Record button with custom style
        self.recordStartButton = cmds.button(l='Start Recording', w=50, command=self._checkRecordingStart)
        recordButton = wrapInstance(long(OpenMayaUI.MQtUtil.findControl(self.recordStartButton)), QtWidgets.QPushButton)
        recordButton.setStyleSheet(
            "QPushButton:disabled {"
                "background-color: rgb(75, 75, 75) }"
            "QPushButton {"
                "background-color: rgb(200, 10, 10);"
                "border-style: outset;"
                "border-width: 0px;"
                "border-radius: 5px;"
                "border-color: beige;"
                #"font: bold 14px;"
                "min-width: 10em;"
                "padding: 6px; }"
            "QPushButton:hover {"
                "background-color: rgb(225, 10, 10) }"
            "QPushButton:pressed {" 
                "background-color: rgb(100, 10, 10) }")

        self.recordStopButton = cmds.button(l='Stop Recording', w=50, command=partial(self._recording, False))
        cmds.separator(h=5, style='none')
        self.runMacroButton = cmds.button(l='Run', w=50, command=self._runMacroButton)
        self.macroQuickEditButton = cmds.button(l='Quick Edit', w=50, command=self._macroQuickEditButton)
        self.clearMacroButton = cmds.button(l='Clear', w=50, command=self._clearMacroButton)
        self.deleteMacroButton = cmds.button(l='Delete', w=50, command=self._deleteMacroButton)
        cmds.setParent('..')

        # Right Side Scroll Field
        self.macroScrollField = cmds.scrollField(
            editable=False,
            backgroundColor=self.scrollFieldIDisabledBGColor,
            wordWrap=False,
            p=layout,
            w=150)

        # Right Side Buttons
        self.macroEditButton = cmds.button(l='Edit', p=layout, w=40, command=self._editButton)
        self.macroSaveEditButton = cmds.button(l='Save', p=layout, w=40, command=self._saveButton)
        self.macroUndoEditButton = cmds.button(l='Undo', p=layout, w=40, command=self._undoButton)
        self.macroRedoEditButton = cmds.button(l='Redo', p=layout, w=40, command=self._redoButton)
        self.macroCancelEditButton = cmds.button(l='Cancel', p=layout, w=40, command=self._cancelButton)
        self.macroCopyToClipboardButton = cmds.button(l='Copy', p=layout, w=40, command=self._copyToClipboardButton)

        # Create Layout
        # Left Column
        cmds.formLayout(layout, e=True, af=(leftColumn, 'top', 5))
        cmds.formLayout(layout, e=True, af=(leftColumn, 'left', 5))

        # Scroll Field
        cmds.formLayout(layout, e=True, aoc=(self.macroScrollField, 'top', 0, leftColumn))
        cmds.formLayout(layout, e=True, ac=(self.macroScrollField, 'left', 5, leftColumn))
        cmds.formLayout(layout, e=True, af=(self.macroScrollField, 'bottom', 40))
        cmds.formLayout(layout, e=True, af=(self.macroScrollField, 'right', 5))

        # Copy to Clipboard
        cmds.formLayout(layout, e=True, af=(self.macroCopyToClipboardButton, 'top', 10))
        cmds.formLayout(layout, e=True, af=(self.macroCopyToClipboardButton, 'right', 10))

        # Edit Button
        cmds.formLayout(layout, e=True, aoc=(self.macroEditButton, 'bottom', -30, self.macroScrollField))
        cmds.formLayout(layout, e=True, ac=(self.macroEditButton, 'left', 5, leftColumn))

        # Save Button
        cmds.formLayout(layout, e=True, aoc=(self.macroSaveEditButton, 'top', 0, self.macroEditButton))
        cmds.formLayout(layout, e=True, ac=(self.macroSaveEditButton, 'left', 5, self.macroEditButton))

        # Undo Button
        cmds.formLayout(layout, e=True, aoc=(self.macroUndoEditButton, 'top', 0, self.macroEditButton))
        cmds.formLayout(layout, e=True, ac=(self.macroUndoEditButton, 'left', 5, self.macroSaveEditButton))

        # Redo Button
        cmds.formLayout(layout, e=True, aoc=(self.macroRedoEditButton, 'top', 0, self.macroEditButton))
        cmds.formLayout(layout, e=True, ac=(self.macroRedoEditButton, 'left', 5, self.macroUndoEditButton))

        # Cancel Button
        cmds.formLayout(layout, e=True, aoc=(self.macroCancelEditButton, 'bottom', -30, self.macroScrollField))
        cmds.formLayout(layout, e=True, af=(self.macroCancelEditButton, 'right', 5))

        # Refresh the macro list
        self._listMacros()
        self._loadMacroButton()

        cmds.showWindow(self.window)

    def _debugButton(self, *args):
        """
        Debugging button, handy for testing
        """
        if self.toggleColor:
            recordButton = wrapInstance(long(OpenMayaUI.MQtUtil.findControl(self.recordStartButton)), QtWidgets.QPushButton)
            recordButton.setStyleSheet(
                "QPushButton:disabled {"
                "background-color: rgb(75, 75, 75) }"
                "QPushButton {"
                "background-color: rgb(10, 200, 10);"
                "border-style: outset;"
                "border-width: 0px;"
                "border-radius: 5px;"
                "border-color: beige;"
                # "font: bold 14px;"
                "min-width: 10em;"
                "padding: 6px; }"
                "QPushButton:hover {"
                "background-color: rgb(10, 225, 10) }"
                "QPushButton:pressed {"
                "background-color: rgb(10, 100, 10) }")
            self.toggleColor = False
        else:
            recordButton = wrapInstance(long(OpenMayaUI.MQtUtil.findControl(self.recordStartButton)), QtWidgets.QPushButton)
            recordButton.setStyleSheet(
                "QPushButton:disabled {"
                "background-color: rgb(75, 75, 75) }"
                "QPushButton {"
                "background-color: rgb(200, 10, 10);"
                "border-style: outset;"
                "border-width: 0px;"
                "border-radius: 5px;"
                "border-color: beige;"
                # "font: bold 14px;"
                "min-width: 10em;"
                "padding: 6px; }"
                "QPushButton:hover {"
                "background-color: rgb(225, 10, 10) }"
                "QPushButton:pressed {"
                "background-color: rgb(100, 10, 10) }")
            self.toggleColor = True

    @staticmethod
    def _clamp(value, min, max):
        if value < min:
            return min
        elif value > max:
            return max
        else:
            return value

    def _copyToClipboardButton(self, *args):
        """
        Copy the active macro to the the clipboard
        """
        print('_copyToClipboardButton')

    def _macroQuickEditButton(self, *args):
        """
        Toggle quick edit mode to remove lines of code
        """
        print('_macroQuickEditButton')

    def _undoButton(self, *args):
        """
        Save the last string in the list of backups to the active macro, decrementing
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
        Save the next string in the list of backups to the active macro, incrementing
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
        Disable or enable the redo and undo buttons depending on the current backup index
        """
        index = self.backUpsIndex
        length = len(self.activeMacroBackUps)

        # Disable Undo
        if index <= 1:
            cmds.button(self.macroUndoEditButton, e=True, enable=False)
        # Enable Undo
        else:
            cmds.button(self.macroUndoEditButton, e=True, enable=True)

        if index >= length:
            cmds.button(self.macroRedoEditButton, e=True, enable=False)
        else:
            cmds.button(self.macroRedoEditButton, e=True, enable=True)

    def _editButton(self, *args):
        """
        Enable editing of the scroll field window
        """
        # self._addActiveMacroBackUp()
        cmds.scrollField(self.macroScrollField, e=True, editable=True, backgroundColor=self.scrollFieldActiveBGColor)

    def _saveButton(self, *args):
        """
        Save the current scrollField text to the active macro
        """
        self._addActiveMacroBackUp()
        newText = cmds.scrollField(self.macroScrollField, q=True, text=True)
        self._saveStringToMacro(newText)
        self._addActiveMacroBackUp()

    def _cancelButton(self, *args):
        """
        Reset the scroll field
        """
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
        icon = 'question'
        message = ' already exists. Do you want to replace it?'  # Macro name is added to message

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
            self._toggleActiveUI(enable=False, includeStopButton=False)
            #cmds.button(self.recordStartButton, e=True, backgroundColor=self.recordStartButtonColor)

            # Set the active macro to the console readout file
            cmds.scriptEditorInfo(historyFilename=self.activeMacroPath)
            print('recording started...')
            cmds.scriptEditorInfo(clearHistory=True, writeHistory=True)

        # Stop recording
        elif recording is False:
            if self.recording is False:
                return
            self.recording = False

            # Stop recording
            cmds.scriptEditorInfo(writeHistory=False)
            self.openMacroFile.close()
            self._resetConsoleSettings()

            # enable UI
            self._toggleActiveUI(enable=True)
            #cmds.button(self.recordStartButton, e=True, backgroundColor=self.buttonDefaultColor)

            # Review the recording in the scroll field
            self._resetMacroScrollField()

            print('recording stopped...')

    def _checkRecordingStart(self, *args):
        """
        Check the active macro before recording,
        ask for user input if the file is not empty
        """
        # Ask user if they want to overwrite the active file and start recording
        with open(self.activeMacroPath) as self.openMacroFile:
            if self.openMacroFile.read():
                self._recording(True)
            # The active file is empty, start recording
            else:
                self._recording(True)
                return

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
        cmds.button(self.runMacroButton, e=True, en=enable)
        cmds.button(self.clearMacroButton, e=True, en=enable)
        cmds.button(self.deleteMacroButton, e=True, en=enable)
        cmds.button(self.macroEditButton, e=True, en=enable)
        cmds.button(self.macroUndoEditButton, e=True, en=enable)
        cmds.button(self.macroRedoEditButton, e=True, en=enable)
        cmds.button(self.macroSaveEditButton, e=True, en=enable)
        cmds.button(self.macroCopyToClipboardButton, e=True, en=enable)
        cmds.button(self.macroCancelEditButton, e=True, en=enable)
        cmds.button(self.macroQuickEditButton, e=True, en=enable)

    def _runMacroButton(self, *args):
        """
        Playback the active macro
        """
        print('playing back last recording...' + '\n')
        mel.eval('source \"' + self.activeMacroPath + '\";')
        print('playback finished...')

    def _clearMacroButton(self, *args):
        """
        Clears the contents from the active macro
        """
        # Dialog Message Contents
        title = 'Clear Macro'
        icon = 'question'
        message = 'The macro \"' + self.activeMacro + '\" will be cleared of all contents, do you wish to continue?'

        # Add backup before clearing
        self._addActiveMacroBackUp()

        # Clear the active macro after confirming with the user
        with open(self.activeMacroPath) as openMacroFile:
            if openMacroFile.read():
                # User Confirmation
                if self._dialogBool(title, message, icon) is True:
                    open(self.activeMacroPath, 'w').close()
                    self._resetMacroScrollField()

    # TODO: Add comments
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

    # TODO: Add comments
    def _listMacros(self, *args):
        """
        refresh the option menu to
        show all available characters
        """
        items = cmds.optionMenu(self.macroOption, q=True, ill=True)
        if items is not None:
            cmds.deleteUI(items)

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
        Load the name of the selected macro which is stored in the description file,
        then show the macro in the scroll field. Activate the buttons if a valid macro is loaded
        """
        enable = False

        if cmds.optionMenu(self.macroOption, q=True, sl=True) != 1:
            self.activeMacro = cmds.optionMenu(self.macroOption, q=True, v=True)
            self.activeMacroPath = self.macroFolderPath + '/' + self.macroPrefix + self.activeMacro + ".txt"
            # print('// Loaded Macro \'%s\' from \'%s\'' % (self.activeMacro, self.activeMacroPath))
            self._resetMacroScrollField()

            # Clear any backups from previous active macro and add an initial backup
            del self.activeMacroBackUps[:]
            self.backUpsIndex = 0

            enable = True

        # Turn off the UI elements that require an active macro
        # do not include the create macro UI
        self._toggleActiveUI(enable, False)
        self._updateUndoRedoButtonStates()

        # Clear the active macro if no macro is selected from the list
        if not enable:
            self.activeMacro = ''

    # TODO: Add comments
    def _addActiveMacroBackUp(self):
        """
        Get and Set the macro back up here, only add unique entries
        """
        with open(self.activeMacroPath) as openMacroFile:
            newBackUp = openMacroFile.read()
            if len(self.activeMacroBackUps) != 0:
                previousBackUp = ''.join(map(str, self.activeMacroBackUps[-1:]))
                if previousBackUp != newBackUp and newBackUp is not False:
                    self.activeMacroBackUps.append(newBackUp)
                    self.backUpsIndex += 1
                    self._updateUndoRedoButtonStates()
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
