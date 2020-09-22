# noinspection SpellCheckingInspection
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from functools import partial
import os

# TODO: FEATURE WISHLIST
#       1) live updating of scroll field text as output is recorded
#       2) append recording from any line "start new recording at line X"
#       3) delete line by line with buttons
#       4) add nice number formatting on left side of scroll field
#       5) bind keys to macros ie "press shift + 6 and macro6 runs"
#       6) [DONE] give placeholder edit/save/cancel buttons real functionality
#       7) Add warnings for editing/saving/cancelling
#       8) figure out how to get maya console output without writing to a file
#       9) [NEXT] debug the console output options, they don't seem to be working

class MacroTools:

    def __init__(self):
        self.win = 'macroRecorderWindow'
        self.macroFolderPath = 'C:/Users/Brooke/Desktop/Macros'
        self.macroPrefix = ''  # No prefix
        self.recording = False

        # UI
        self.createMacroButton = ''
        self.debugButton = ''
        self.recordStartButton = ''
        self.recordStopButton = ''
        self.runMacroButton = ''
        self.deleteMacroButton = ''
        self.macroEditButton = ''
        self.macroSaveEditButton = ''
        self.macroCancelEditButton = ''
        self.macroFileField = ''
        self.macroScrollField = ''
        # self.scrollFieldDefaultBGColor = (0.1686, 0.1686, 0.1686)
        self.scrollFieldActiveBGColor = (0.1, 0.1, 0.1)
        self.scrollFieldIDisabledBGColor = (0.225, 0.225, 0.225)

        # TODO: Organize these variables to be clearer
        self.activeMacro = ''
        self.activeMacroPath = ''

        self.newMacroFile = ''
        self.newMacroPath = ''

        self.macrosFolderPath = ''
        self.macroOption = ''

        self.macroEditBackUp = ''

        # Script Editor Output Settings
        self.old_echoAllLines = ''
        self.old_showLineNumbersIsOn = ''
        self.old_stackTraceIsOn = ''
        self.old_commandReporterCmdScrollFieldReporter1SuppressResults = ''
        self.old_commandReporterCmdScrollFieldReporter1SuppressInfo = ''
        self.old_commandReporterCmdScrollFieldReporter1SuppressWarnings = ''
        self.old_commandReporterCmdScrollFieldReporter1SuppressErrors = ''
        self.old_commandReporterCmdScrollFieldReporter1SuppressStackTrace = ''

        self._buildUI()

    def _buildUI(self):
        """
        Create the macro tool window
        """
        # Window Settings
        # If the window already exists delete the existing UI before drawing it again
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win)

        # Set the window size
        if cmds.windowPref(self.win, exists=True):
            cmds.windowPref(self.win, e=True, w=600, h=150)

        mainWindow = cmds.window(self.win, t='MacroRecorder', w=600, h=150, menuBar=True)
        layout = cmds.formLayout(p=mainWindow)

        # Left Column UI
        leftColumn = cmds.columnLayout(adjustableColumn=True, p=layout, w=300)

        # Debug Button
        self.debugButton = cmds.button(label='Debug Button', w=50, command=self._debugButton)

        # Create Macros
        cmds.frameLayout(label='Create Macro', marginWidth=10, marginHeight=10)
        self.macroFileField = cmds.textFieldButtonGrp(label='Macro File' + self.macroPrefix,
                                                      buttonLabel='...',
                                                      cw3=(60, 160, 30),
                                                      co3=(0, 5, 0),
                                                      ct3=('both', 'both', 'both'), bc=partial(self._openFileList))

        self.createMacroButton = cmds.button(label='Create New Macro', w=50, command=self._createMacro)
        cmds.separator(h=5, style='none')
        cmds.setParent('..')

        # Active Macro Options
        cmds.frameLayout(label='Active Macro Options', marginWidth=10, marginHeight=10)
        self.macroOption = cmds.optionMenu(cc=partial(self._loadMacro))
        cmds.separator(h=5, style='doubleDash')
        self.recordStartButton = cmds.button(label='Start Recording', w=50, command=self._recordingStart)
        self.recordStopButton = cmds.button(label='Stop Recording', w=50, command=self._recordingStop)
        cmds.separator(h=5, style='none')
        self.runMacroButton = cmds.button(label='Run', w=50, command=self._runMacro)
        self.deleteMacroButton = cmds.button(label='Delete', w=50, command=self._deleteMacro)
        cmds.setParent('..')

        # Right Side UI
        self.macroScrollField = cmds.scrollField(editable=False, wordWrap=True, p=layout, w=150)
        self.macroEditButton = \
            cmds.button(l='Edit', p=layout, w=50, command=partial(self._toggleEditScrollField, True))
        self.macroSaveEditButton = \
            cmds.button(l='Save', p=layout, w=50, command=self._saveScrollFieldEditsToMacro)
        self.macroCancelEditButton = \
            cmds.button(l='Cancel', p=layout, w=50, command=partial(self._toggleEditScrollField, False))

        # Create Layout
        # Left Column
        cmds.formLayout(layout, e=True, af=(leftColumn, 'top', 5))
        cmds.formLayout(layout, e=True, af=(leftColumn, 'left', 5))

        # # Scroll Field
        cmds.formLayout(layout, e=True, aoc=(self.macroScrollField, 'top', 0, leftColumn))
        cmds.formLayout(layout, e=True, ac=(self.macroScrollField, 'left', 5, leftColumn))
        cmds.formLayout(layout, e=True, af=(self.macroScrollField, 'bottom', 40))
        cmds.formLayout(layout, e=True, af=(self.macroScrollField, 'right', 5))

        # Edit Button
        cmds.formLayout(layout, e=True, aoc=(self.macroEditButton, 'bottom', -30, self.macroScrollField))
        cmds.formLayout(layout, e=True, ac=(self.macroEditButton, 'left', 5, leftColumn))

        # Save Button
        cmds.formLayout(layout, e=True, aoc=(self.macroSaveEditButton, 'top', 0, self.macroEditButton))
        cmds.formLayout(layout, e=True, ac=(self.macroSaveEditButton, 'left', 5, self.macroEditButton))

        # Cancel Button
        cmds.formLayout(layout, e=True, aoc=(self.macroCancelEditButton, 'bottom', -30, self.macroScrollField))
        cmds.formLayout(layout, e=True, af=(self.macroCancelEditButton, 'right', 5))

        # Refresh the macro list
        self._listMacros()
        self._loadMacro()

        cmds.showWindow(mainWindow)

    def _debugButton(self, *args):
        """
        Debugging button, handy for testing
        """
        var = cmds.scriptEditorInfo(q=True, input=True)
        print()

    def _saveScrollFieldEditsToMacro(self, *args):
        """
        Save edits in the scrollField to the active macro.
        """
        newText = cmds.scrollField(self.macroScrollField, q=True, text=True)
        with open(self.activeMacroPath, 'w') as openMacroFile:
            print(newText)
            print(openMacroFile.mode)
            openMacroFile.write(newText)

        self._toggleEditScrollField(False, True)

    def _toggleEditScrollField(self, enable=True, savingChanges=True, *args):
        """
        Editing settings for the scrollField
        """
        # Enable Editing
        if enable:
            cmds.scrollField(self.macroScrollField, e=True,
                             editable=True,
                             backgroundColor=self.scrollFieldActiveBGColor)
        # Cancel Editing
        elif savingChanges is False:
            cmds.scrollField(self.macroScrollField, e=True,
                             editable=False,
                             backgroundColor=self.scrollFieldIDisabledBGColor,
                             text=self.macroEditBackUp)
        # Save Edits
        else:
            cmds.scrollField(self.macroScrollField, e=True,
                             editable=False,
                             backgroundColor=self.scrollFieldIDisabledBGColor)

    def _createMacro(self, *args):
        """
        Create a new blank macro from the macroFileField
        """
        # TODO: Make these conditionals clearer
        macroFileFieldText = cmds.textFieldButtonGrp(self.macroFileField, q=True, tx=True)
        if macroFileFieldText:
            for macro in self._getMacros():
                if macro.split('.txt')[0] == macroFileFieldText:
                    dialogMessage = macro + ' already exists. Do you want to replace it?'
                    if self._dialogBool('Create Macro', dialogMessage, 'question'):
                        # Create Macro
                        newMacroName = cmds.textFieldButtonGrp(self.macroFileField, q=True, tx=True)
                        self.newMacroPath = self.macroFolderPath + '/' + self.macroPrefix + newMacroName + '.txt'
                        self.newMacroFile = open(self.newMacroPath, 'w')
                        self.newMacroFile.close()

                        # Refresh the macro list
                        self._listMacros()
                        self._loadMacro()
                        return
                    else:
                        return

            newMacroName = cmds.textFieldButtonGrp(self.macroFileField, q=True, tx=True)
            self.newMacroPath = self.macroFolderPath + '/' + self.macroPrefix + newMacroName + '.txt'
            self.newMacroFile = open(self.newMacroPath, 'w')
            self.newMacroFile.close()
            print('New macro created: ' + self.newMacroPath)

            # Refresh the macro list
            self._listMacros()

            # Make the new macro the active macro
            cmds.optionMenu(self.macroOption, e=True, v=newMacroName)

            self._loadMacro()
        else:
            OpenMaya.MGlobal_displayError('No new macro file is defined')

    def _deleteMacro(self, *args):
        """
        Delete the active macro
        """
        if self.activeMacro:
            confirm = cmds.confirmDialog(title='Delete Macro',
                                         message='Delete the macro \"' + self.activeMacro + '\"?',
                                         button=['Delete', 'Cancel'],
                                         defaultButton='Delete',
                                         cancelButton='Cancel',
                                         dismissString='Cancel',
                                         icon='warning')
        else:
            OpenMaya.MGlobal_displayError('No new macro file is defined')
            return

        if confirm == 'Delete':
            # Delete the active file
            os.remove(self.activeMacroPath)

            # Refresh the macro list
            self._listMacros()
            self._loadMacro()
        elif confirm == 'Cancel':
            return

    def _openFileList(self, *args):
        """
        Open a file dialog for letting the user choose a file for saving the macro
        """
        fileName = cmds.fileDialog2(dir=self.macroFolderPath, fileMode=0, fileFilter='Text Files (*.txt)',
                                    okCaption='OK', caption='Select or Create a %s File' % 'New Macro')
        # Add prefix to file name
        prefixAdded = fileName[0].replace(os.path.basename(fileName[0]),
                                          self.macroPrefix + os.path.basename(fileName[0]))
        self.newMacroPath = prefixAdded
        print(self.newMacroPath)

        if not self.newMacroPath:
            return

        # Update field with new macro name
        cmds.textFieldButtonGrp(self.macroFileField, e=True,
                                text=os.path.basename(self.newMacroPath).split('.')[0])

    def _recordingStart(self, *args):
        """
        Record the script editor output to the active macro
        """
        title = 'Overwrite Macro'
        icon = 'warning'
        message = self.activeMacro + \
                  ' is not empty. Starting a recording will' \
                  ' overwrite the contents. Do you wish to continue?'

        with open(self.activeMacroPath) as openMacroFile:
            if openMacroFile.read():
                # Ask user to overwrite the active file and start recording
                if self._dialogBool(title, message, icon):
                    self._saveConsoleSettings()
                    self._setConsoleRecordingSettings()
                    self.toggleActiveUI(enable=False)
                    cmds.scriptEditorInfo(historyFilename=self.activeMacroPath)

                    print('recording started...')

                    self.activeMacro = open(self.activeMacroPath, 'w')
                    cmds.scriptEditorInfo(clearHistory=True, writeHistory=True)
                # Cancel recording
                else:
                    print('recording canceled')
                    return
            # The active file is empty, start recording
            else:
                self._saveConsoleSettings()
                self._setConsoleRecordingSettings()
                self.toggleActiveUI(enable=False)
                cmds.scriptEditorInfo(historyFilename=self.activeMacroPath)

                print('recording started...')

                self.activeMacro = open(self.activeMacroPath, 'w')
                cmds.scriptEditorInfo(clearHistory=True, writeHistory=True)
                return

    # TODO: Only stop recording if we are recording, need a bool here.
    def _recordingStop(self, *args):
        """
        Stop recording the script editor output to the active macro
        """
        # Stop recording
        cmds.scriptEditorInfo(writeHistory=False)
        self.activeMacro.close()
        self._resetConsoleSettings()

        # enable UI
        self.toggleActiveUI(enable=True)

        # Review the recording in the scroll field
        self._updateMacroScrollField()

        print('recording stopped...')

    def toggleActiveUI(self, enable):
        """
        Toggle the UI off/on, mainly used for recording
        """
        cmds.textFieldButtonGrp(self.macroFileField, e=True, en=enable)
        cmds.optionMenu(self.macroOption, e=True, en=enable)
        cmds.button(self.recordStartButton, e=True, en=enable)
        cmds.button(self.createMacroButton, e=True, en=enable)
        cmds.button(self.runMacroButton, e=True, en=enable)
        cmds.button(self.deleteMacroButton, e=True, en=enable)
        cmds.button(self.macroEditButton, e=True, en=enable)
        cmds.button(self.macroSaveEditButton, e=True, en=enable)
        cmds.button(self.macroCancelEditButton, e=True, en=enable)

    def _runMacro(self, *args):
        """
        playback the active macro
        """
        print('playing back last recording...')
        with open(self.activeMacroPath) as openMacroFile:
            print(openMacroFile.read())
        print('playback finished...')

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

    def _loadMacro(self, *args):
        """
        Load the name of the selected macro which is stored in the description file,
        then show the macro in the scroll field. Activate the buttons if a valid character is loaded
        """
        enable = False

        if cmds.optionMenu(self.macroOption, q=True, sl=True) != 1:
            self.activeMacro = cmds.optionMenu(self.macroOption, q=True, v=True)
            self.activeMacroPath = self.macroFolderPath + '/' + self.macroPrefix + self.activeMacro + ".txt"
            print('// Loaded Macro \'%s\' from \'%s\'' % (self.activeMacro, self.activeMacroPath))

            self._updateMacroScrollField()

            enable = True

        # Set the buttons enabled state
        cmds.button(self.recordStartButton, e=True, en=enable)
        cmds.button(self.recordStopButton, e=True, en=enable)
        cmds.button(self.runMacroButton, e=True, en=enable)
        cmds.button(self.deleteMacroButton, e=True, en=enable)

        # Clear the active macro if no macro is selected from the list
        if not enable:
            self.activeMacro = ''

    def _updateMacroScrollField(self):
        """
        Load the active macro to the macroScrollField, disable
        the scroll field and create a backup of the macro
        """
        with open(self.activeMacroPath) as openMacroFile:
            macroText = openMacroFile.read()
            self.macroEditBackUp = macroText
            cmds.scrollField(self.macroScrollField, e=True,
                             editable=False,
                             backgroundColor=self.scrollFieldIDisabledBGColor,
                             text=macroText)

    # @staticmethod
    # def _writeDescription(path, data):
    #     """
    #     write a text file with the given data to the given path
    #     """
    #     try:
    #         file = open(path, 'wb')
    #     except:
    #         OpenMaya.MGlobal_displayError('A file error has occurred for file \'%s\'' % path)
    #         return
    #     file.write(str(data) + '\n')
    #     file.close()
    #
    # @staticmethod
    # def _readDescription(path):
    #     """
    #     read a text file at the given path and return a list of lines
    #     """
    #     try:
    #         file = open(path, 'rb')
    #     except:
    #         OpenMaya.MGlobal_displayError('A file error has occurred for file \'%s\'' % path)
    #         return
    #     data = file.read()
    #     lines = data.split('\n')
    #     file.close()
    #     return lines

    @staticmethod
    def _dialogBool(title, message, icon):
        """
        Return True/False after asking for user input, simplified for when Yes/No is sufficient
        """
        result = cmds.confirmDialog(title=title,
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
        cmds.optionVar(iv=('echoAllLines', 0))
        cmds.optionVar(iv=('showLineNumbersIsOn', 0))
        cmds.optionVar(iv=('stackTraceIsOn', 0))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressResults', 1))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressInfo', 1))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressWarnings', 1))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressErrors', 1))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressStackTrace', 1))

    def _resetConsoleSettings(self):
        """
        Set the console output settings to their original saved value
        """
        cmds.optionVar(iv=('echoAllLines', int(self.old_echoAllLines)))
        cmds.optionVar(iv=('showLineNumbersIsOn', self.old_showLineNumbersIsOn))
        cmds.optionVar(iv=('stackTraceIsOn', self.old_stackTraceIsOn))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressResults',
                           self.old_commandReporterCmdScrollFieldReporter1SuppressResults))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressInfo',
                           self.old_commandReporterCmdScrollFieldReporter1SuppressInfo))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressWarnings',
                           self.old_commandReporterCmdScrollFieldReporter1SuppressWarnings))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressErrors',
                           self.old_commandReporterCmdScrollFieldReporter1SuppressErrors))
        cmds.optionVar(iv=('commandReporterCmdScrollFieldReporter1SuppressStackTrace',
                           self.old_commandReporterCmdScrollFieldReporter1SuppressStackTrace))

    def _saveConsoleSettings(self):
        """
        Save the current settings of the console output
        """
        self.old_echoAllLines = cmds.optionVar(q='echoAllLines')
        self.old_showLineNumbersIsOn = cmds.optionVar(q='showLineNumbersIsOn')
        self.old_stackTraceIsOn = cmds.optionVar(q='stackTraceIsOn')
        self.old_commandReporterCmdScrollFieldReporter1SuppressResults = cmds.optionVar(
            q='commandReporterCmdScrollFieldReporter1SuppressResults')
        self.old_commandReporterCmdScrollFieldReporter1SuppressInfo = cmds.optionVar(
            q='commandReporterCmdScrollFieldReporter1SuppressInfo')
        self.old_commandReporterCmdScrollFieldReporter1SuppressWarnings = cmds.optionVar(
            q='commandReporterCmdScrollFieldReporter1SuppressWarnings')
        self.old_commandReporterCmdScrollFieldReporter1SuppressErrors = cmds.optionVar(
            q='commandReporterCmdScrollFieldReporter1SuppressErrors')
        self.old_commandReporterCmdScrollFieldReporter1SuppressStackTrace = cmds.optionVar(
            q='commandReporterCmdScrollFieldReporter1SuppressStackTrace')
