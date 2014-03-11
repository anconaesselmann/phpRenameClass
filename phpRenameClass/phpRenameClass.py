import sublime
import sublime_plugin
import re
from functools import partial
import os
import shutil


PACKAGE_NAME = "phpRenameClass"

settings = sublime.load_settings(PACKAGE_NAME+ '.sublime-settings')

class ReplaceViewContentCommand(sublime_plugin.TextCommand):
    def run(self, edit, string=''):
        self.view.erase(edit, sublime.Region(0, self.view.size()))
        self.view.insert(edit, self.view.size(), string)

class phpRenameClassCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.getOldClassName()

    def execute(self):
        filesToRename = self.util.getFilesToRename(self.directory)
        for oldFile, newFile in filesToRename:
            message = "Would you like to rename file:\n\n" + oldFile + "\n\n to \n\n" + newFile + "?\n\nExisting files will be overwritten. This can not be undone."
            response = sublime.ok_cancel_dialog(message)
            if response == True:
                self.util.renameFile(oldFile, newFile)

        self.changeFileContent()

    def renameFiles(self):
        return self.util.renameFiles(self.directory)

    def changeFileContent(self):
        files = self.util.getFileNames(self.directory)
        if files:
            sublime.run_command("new_window")
            window = sublime.active_window()
            for f in files:
                view = window.open_file(f)
                sublime.set_timeout(lambda view=view: self.openHandel(view), 100)

    def openHandel(self, view):
        body = view.substr(sublime.Region(0, view.size()))
        newBody = self.util.replace(body)
        sublime.set_timeout(lambda: view.run_command('replace_view_content', {"string": newBody}), 100)

    def getOldClassName(self):
        caption = "Type in the name of the old class."

        view = sublime.Window.active_view(sublime.active_window())
        content = view.substr(sublime.Region(0, view.size()))
        if content:
            namespace, className = phpRenameClass.namespaceAndClassFromFile(content)
            self.initial = namespace + className
        else:
            self.initial = ""

        if not self.initial:
            self.initial = ""
        
        self.inputPanelView = self.window.show_input_panel(
            caption, self.initial,
            self.old_on_done, self.old_on_change, self.old_on_cancel
        )
        self.inputPanelView.set_name("InputPanel")
        self.inputPanelView.settings().set("caret_style", "solid")
    
    def old_on_done(self, inputString):
        view = self.window.active_view()
        self.oldClassName = inputString
        self.getNewClassName()

    def old_on_change(self, command_string):
        pass

    def old_on_cancel(self):
        pass

    def getNewClassName(self):
        caption = "Type in the new name for the class."
        self.inputPanelView = self.window.show_input_panel(
            caption, self.initial,
            self.new_on_done, self.new_on_change, self.new_on_cancel
        )
        self.inputPanelView.set_name("InputPanel")
        self.inputPanelView.settings().set("caret_style", "solid")

    
    def new_on_done(self, inputString):
        view = self.window.active_view()
        self.newClassName = inputString
        try:
            self.util = phpRenameClass(self.oldClassName, self.newClassName)
        except Exception as e:
            sublime.error_message("The old and new class names have to be fully name-spaced.")
        else:
            self.getDirName()

    def new_on_change(self, command_string):
        pass

    def new_on_cancel(self):
        pass

    def getDirName(self):
        caption = "The root directory."

        initial = settings.get('default_path')
        if not isinstance(initial, str):
            initial = ""
        self.inputPanelView = self.window.show_input_panel(
            caption, initial,
            self.dir_on_done, self.dir_on_change, self.dir_on_cancel
        )
        self.inputPanelView.set_name("phpRenameClass")
        self.inputPanelView.settings().set("caret_style", "solid")

        statusMessage = "    Changes will apply to this directory and all subdirectories. Set a default in your user settings for phpRenameClass.    "
        view = self.window.active_view()
        view.set_status("phpRenameClass", statusMessage)
    
    def dir_on_done(self, inputString):
        view = self.window.active_view()
        self.directory = inputString
        view.erase_status("phpRenameClass")
        self.execute()

    def dir_on_change(self, command_string):
        pass

    def dir_on_cancel(self):
        view = self.window.active_view()
        view.erase_status("phpRenameClass")
        pass


class phpRenameClass:
    def __init__(self, classNameNS, newClassNameNS):
        self.namespace, self.className = self.getNamespace(classNameNS)
        self.newNamespace, self.newClassName = self.getNamespace(newClassNameNS)

        self.compiledExpressionInsideNamespace = re.compile(r"""
            (?P<beforeNamespace>(^|[\n\r]+)namespace\s+)
            (""" + re.escape(self.namespace) + r""")
            (?P<afterNamespace>\s+\{)
            (?P<nameSpaceBody>.+)
        """, re.S|re.X)

        self.compiledExpressionFullyNamespaced = re.compile(r"""
            (?<=\s\\)""" + re.escape(self.namespace) + r"""\\""" + self.className + r"""(?=\s|\(|\:\:|Test\s)
        """, re.S|re.X)

    def getNamespace(self, classNameNS):
        classNamePos = classNameNS.rfind("\\")
        if classNamePos < 0:
            raise Exception("Use Namespaces")
        className = re.escape(classNameNS[classNamePos + 1:])
        namespace = classNameNS[:classNamePos]
        return namespace, className

    def replace(self, string):
        string = re.sub(self.compiledExpressionInsideNamespace, partial(insideNamespaceCallback, className=self.className, newNamespace=self.newNamespace, newClassName=self.newClassName), string)
        string = re.sub(self.compiledExpressionFullyNamespaced, re.escape(self.newNamespace) + "\\\\" + self.newClassName, string)
        return string

    def hasMatches(self, directory):
        result = False;
        temp, extension = os.path.splitext(directory)
        if extension == ".php":
            try:
                fileContent = open(directory, 'r').read()

                compiledExpressionClassInsideNS = re.compile(r"""
                    (^|[\n\r]+namespace\s+)""" + 
                    re.escape(self.namespace) + r"""
                    (\s+\{.*\s)""" + 
                    self.className + r"""
                    (?=\s|\(|\:\:|Test\s)
                """, re.S|re.X)

                if re.search(compiledExpressionClassInsideNS, fileContent):
                    result = True
                if re.search(self.compiledExpressionFullyNamespaced, fileContent):
                    result = True
            except Exception as e:
                print("Error reading file " + directory)

        return result



    def getFileNames(self, directory):
        result = []
        for root, dirs, files in os.walk(directory):
            for f in files:
                fileName = os.path.join(root, f);
                if self.hasMatches(fileName):
                    result.append(fileName)
        return result

    def renameFile(self, oldFile, newFile):
        parentDir = os.path.dirname(newFile)
        if not os.path.exists(parentDir):
            os.makedirs(parentDir)
        shutil.move(oldFile, newFile)

    def renameFiles(self, directory):
        result = False
        files = self.getFilesToRename(directory);
        for oldFile, newFile in files:
            self.renameFile(oldFile, newFile)
            result = True
        return result

    def getFilesToRename(self, directory):
        result = []
        oldNamespaceParts = self.namespace.split("\\")
        newNamespaceParts = self.newNamespace.split("\\")
        oldSubFolder = os.path.join(*oldNamespaceParts)
        newSubFolder = os.path.join(*newNamespaceParts)
        for root, dirs, files in os.walk(directory):
            for f in files:
                fileName = os.path.join(root, f);
                if f == self.className + ".php":
                    nsRoot = root[:root.rfind(oldSubFolder)]
                    newFolder = os.path.join(nsRoot, newSubFolder)
                    result.append((fileName, os.path.join(newFolder, self.newClassName + ".php")))
                if f == self.className + "Test.php":
                    nsRoot = root[:root.rfind(oldSubFolder)]
                    newFolder = os.path.join(nsRoot, newSubFolder)
                    result.append((fileName, os.path.join(newFolder, self.newClassName + "Test.php")))
        return result

    @staticmethod
    def namespaceAndClassFromFile(string):
        compiledExpressionNamespaceAndClass = re.compile(r"""
            (.*?[\n\r])
            (namespace\s+)
            (?P<NameSpace>[\w\\]+)
            (\s+[\n\r]*?\{\s*)
            (
                (\s*[\n\r]*\s*)
                (\/\*)(.+)(\*\/)
                (\s*[\n\r]*\s*)
            )?
            (class\s+)
            (?P<ClassName>[^\s]+)
        """, re.S|re.X)
        match = re.match(compiledExpressionNamespaceAndClass, string)
        if match:
            return match.group("NameSpace") + "\\", match.group("ClassName")
        else:
            return False, False

def insideNamespaceCallback(match, className, newNamespace, newClassName):
        compiledExpression = re.compile(r"""
            (?<=\s)
            (""" + className + r""")
            (?=\s|\(|\:\:|Test\s)
            
        """, re.S|re.X)
        result = re.sub(compiledExpression, newClassName, match.group("nameSpaceBody"))
        return match.group("beforeNamespace") + newNamespace + match.group("afterNamespace") + result


