import os.path
import pdfplumber
import re
import sys
import traceback

from os import getcwd
from gtts import gTTS
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileDialog

from main_window import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow):
    '''MainWindow class'''
    IO_dict = {
        'Input': QDir.currentPath() + "/file_manager/input",
        'Output': QDir.currentPath() + "/file_manager/output"
    }
    text = ''
    user_reg_ex = ''

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.btnVocalize.clicked.connect(self.btnVocalizePressed)
        self.ui.btnVocalize.setDisabled(True)

        self.ui.labelRegEx.setVisible(False)
        self.ui.textEditRegEx.setVisible(False)
        self.ui.btnDirInput.clicked.connect(self.openInputFile)
        self.ui.btnDirOutput.clicked.connect(self.openOutputDir)
        self.ui.lineEditDirOutput.setText(self.IO_dict['Output'])
        self.ui.comboMethod.currentTextChanged.connect(self.applyRegExTextboxVisibility)

    def applyRegExTextboxVisibility(self):
        '''SHows or hide textEditRegEx dependantly on mode combobox state'''
        if self.ui.comboMethod.currentText() == 'RegEx separator':
            self.ui.labelRegEx.setVisible(True)
            self.ui.textEditRegEx.setVisible(True)
        else:
            self.ui.labelRegEx.setVisible(False)
            self.ui.textEditRegEx.setVisible(False)

    def btnVocalizePressed(self):
        '''Checks if chosen directories exsist, read regex if regex mode is chosen and calls self.performVocalize'''
        input_file_path = self.ui.lineEditDirInput.text()
        output_dir_path = self.ui.lineEditDirOutput.text()

        if not os.path.isfile(input_file_path):
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                           "Wrong file directory",
                                           f'Can\'t find file{input_file_path} in decribed directory,\n'
                                           f'Please, change directory and try again',
                                           buttons=QtWidgets.QMessageBox.Ok,
                                           parent=self)
            dialog.exec_()
        elif not os.path.isdir(output_dir_path):
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                           "Wrong directory",
                                           f'Can\'t find {output_dir_path} directory,\n'
                                           f'Please, change directory and try again',
                                           buttons=QtWidgets.QMessageBox.Ok,
                                           parent=self)
            dialog.exec_()
        else:
            mode = self.ui.comboMethod.currentText()
            if mode == 'RegEx separator':
                self.user_reg_ex = str(self.ui.textEditRegEx.toPlainText())
                print(self.user_reg_ex)
            language = self.ui.comboLanguage.currentText()
            self.performVocalize(input_file_path, output_dir_path, mode, language)

    def openInputFile(self):
        '''Open file directory and set it as text into lineEditDirInput, it also calls some additional methods'''
        file_dir, _ = QFileDialog.getOpenFileName(self,
                                               "Выбор текста",
                                               getcwd() + '/file_manager/input',
                                               "Document (*.pdf)"
                                               )
        self.ui.lineEditDirInput.setText(file_dir)
        self.readFile(file_dir)
        self.updatePreviewText()
        self.ui.btnVocalize.setEnabled(True)

    def readFile(self, file_dir):
        '''reads PDF-file and saves text into self.text attribute'''
        with pdfplumber.PDF(open(file=file_dir, mode='rb')) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
            self.text = ''.join(pages)

    def updatePreviewText(self):
        '''Updates plainTextEdit with first 500 symbols of read text'''
        self.ui.plainTextEdit.clear()
        self.ui.plainTextEdit.insertPlainText(self.text if len(self.text) < 500 else self.text[:500])

    def openOutputDir(self):
        '''open directory and set it as text into lineEditDirOutput'''
        file_dir = QFileDialog.getExistingDirectory(self,
                                                    "Open Directory",
                                                    getcwd() + '/file_manager/output',
                                                    QFileDialog.ShowDirsOnly
                                                    )
        self.ui.lineEditDirOutput.setText(file_dir)

    def preproccessText(self, mode):
        '''This method gets chosen by user mode and returns a list of splited by separator blocks(str)'''
        the_book = []
        if mode == 'One file':
            text = self.text.replace('\n', '')
            the_book.append(text)
        elif mode == 'Chapters':
            the_book = list(filter(None, re.split(r'\s*Глава\s*[-+]?\d+\s*', self.text, maxsplit=0)))
            # splitting the string with the word 'Глава' and numbers
        elif mode == 'RegEx separator':
            the_book = list(filter(None, re.split(f'{self.user_reg_ex}', self.text, maxsplit=0)))
            print(the_book, sep='\n')
        else:
            print('wrong mode format')
        return the_book

    def performVocalize(self, input_file_path, output_dir_path, mode, language):
        '''Actually perform vocalization for every splited block in 'the_book'
        and saves it separately for each chapter'''
        counter = 1
        the_book = self.preproccessText(mode)
        for chapter in the_book:
            my_audio = gTTS(text=chapter, lang=language, slow=False)
            file_name = input_file_path[input_file_path.rfind('/') + 1: input_file_path.rfind('.')]
            if mode != 'One file':
                file_name += '_' + str(counter)
                print(file_name)
            my_audio.save(f'{output_dir_path}/{file_name}.mp3')
            status_per_cent = round(counter * 100 / len(the_book), 2)
            print(f'[+] {file_name}.mp3 saved successfully\n {status_per_cent}% completed')
            counter += 1


def excepthook(exc_type, exc_value, exc_tb):
    '''This func shows error text instead of "silent" QT crash'''
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Oбнаружена ошибка !:", tb)

sys.excepthook = excepthook

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
