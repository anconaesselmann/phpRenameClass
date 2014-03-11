import unittest
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.abspath(path.join(__file__, "..", "..")))

from phpRenameClass.phpRenameClass import phpRenameClass
import os
import shutil
#from classes_and_tests.src.mocking.sublime import *

def dataProvider(dataProviderFunction):
    def decorator(testFunction):
        def testRunner(self, *args):
            counter = 1
            allData = dataProviderFunction(self)
            allDataContainerType = allData.__class__.__name__
            if allDataContainerType != "list":
                raise Exception("Data Providers have to return lists. '" + allDataContainerType + "' passed instead.")
            for testCaseArguments in allData:
                containerType = testCaseArguments.__class__.__name__
                if containerType != "list":
                    raise Exception("Data Providers have to return lists of lists. Item " + str(counter) + " in the returned list is of type '" + containerType + "' instead.")
                try:
                    testFunction(self, *testCaseArguments)
                except Exception, e:
                    print("ERROR:\nTest failed with data set " + str(counter) + ":")
                    print(testCaseArguments)
                    raise
                counter += 1
        return testRunner
    return decorator

class phpRenameClassTest(unittest.TestCase):
    def test___init__(self):
        newClassName = "new\\name\\space\\newClassName"
        className = "aae\\ui\\OldNameOfClass"
        obj = phpRenameClass(className, newClassName)

    def dataProvider_replace_inside_namespace(self):
        return [
            [ # data set 1
                "new\\name\\space\\newClassName",
                "aae\\ui\\OldNameOfClass",
                """<?php
namespace aae\ui {
    class OldNameOfClass {
        $test = new OldNameOfClass() {
            $static = OldNameOfClass::$test;
            $instantiation = OldNameOfClass();
        }
    }
}""",           """<?php
namespace new\\name\\space {
    class newClassName {
        $test = new newClassName() {
            $static = newClassName::$test;
            $instantiation = newClassName();
        }
    }
}"""
            ],
            [ # data set 2
                "new\\name\\space\\newClassName",
                "aae\\ui\\OldNameOfClass",
                """<?php
namespace other {
    $instantiation = \\aae\\ui\\OldNameOfClass();
    $shouldNotReplace = \\test\\aae\\ui\\OldNameOfClass();
}
namespace aae\ui {
    class OldNameOfClass {
        $test = new OldNameOfClass() {
            $static = OldNameOfClass::$test;
            $instantiation = OldNameOfClass();
        }
    }
}""" ,           """<?php
namespace other {
    $instantiation = \\new\\name\\space\\newClassName();
    $shouldNotReplace = \\test\\aae\\ui\\OldNameOfClass();
}
namespace new\\name\\space {
    class newClassName {
        $test = new newClassName() {
            $static = newClassName::$test;
            $instantiation = newClassName();
        }
    }
}"""
            ],
        ]

    @dataProvider(dataProvider_replace_inside_namespace)
    def test_replace_inside_namespace(self, newClassName, className, string, expected):
        # Given A string containing php code
        obj = phpRenameClass(className, newClassName)
   
        # When replace is called
        result = obj.replace(string)
        
        # Then the result has all instances of className replaced
        self.assertEqual(expected, result)
    
    '''def test_getFileNames(self):
        # Given a directory name
        newClassName = "new\\name\\space\\newClassName"
        className = "old\\name\\space\\OldNameOfClass"
        obj = phpRenameClass(className, newClassName)
        directory = "/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/pythonTest";
    
        # When getFileNames is called
        result = obj.getFileNames(directory)
        
        # Then return an array with all file names
        expected = []
        self.assertEqual(expected, result)'''
    
    def dataProvider_replace_inside_namespace(self):
        return [
            ["/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest/old/name/space/OldNameOfClass.php",
             True ],
            ["/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest/old/name/other/Other.php",
             False],
            ["/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest/old/name/space/Other.php",
             False],
        ]

    @dataProvider(dataProvider_replace_inside_namespace)
    def test_hasMatches_success(self, directory, expected):
        # Given [SETUP CONDITIONS]
        newClassName = "new\\name\\space\\newClassName"
        className    = "old\\name\\space\\OldNameOfClass"
        obj          = phpRenameClass(className, newClassName)
        # When hasMatches is called
        result = obj.hasMatches(directory)
        
        # Then [EXPECTED CONDITIONS]
        self.assertEqual(expected, result)

    def test_renameFiles(self):
        # Given a root directory, an old an new class name
        newClassName = "new\\name\\space\\newClassName"
        className = "old\\folder\\subFolder\\OldNameOfClass"
        directory = "/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/fileRenamingTest"
        obj = phpRenameClass(className, newClassName)

        oldDir                = path.join(directory, "old")
        oldFolderDir          = path.join(directory, "old", "folder")
        oldFolderSubFolderDir = path.join(directory, "old", "folder", "subFolder")
        oldClassFile          = path.join(directory, "old", "folder", "subFolder", "OldNameOfClass.php")
        newDir                = path.join(directory, "new")
        if path.exists(oldDir):
            shutil.rmtree(oldDir)
        os.makedirs(oldDir)
        os.makedirs(oldFolderDir)
        os.makedirs(oldFolderSubFolderDir)
        open(oldClassFile, 'w+')

        if path.exists(newDir):
            shutil.rmtree(newDir)

        result = obj.renameFiles(directory)

        newFileExists = path.isfile(path.join(directory, "new", "name", "space", "newClassName.php"))
        oldFileExists = path.isfile(oldClassFile)
        
        # Then PSR-0 namespaced Files and folders will be renamed, created and moved
        expected = ""
        self.assertEqual(True, newFileExists)
        self.assertEqual(False, oldFileExists)
        self.assertEqual(True, result)

    def test_getFilesToRename(self):
        # Given a root direcotyr, an old an new class name
        newClassName = "new\\name\\space\\newClassName"
        className = "old\\name\\space\\OldNameOfClass"
        directory = "/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest"
        obj = phpRenameClass(className, newClassName)
    
        # When getFilesToRename is called
        result = obj.getFilesToRename(directory)
       
        self.maxDiff = None
        # Then return a dictionary with files to be renamed, old and new file names
        expected = [
                        ("/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest/old/name/space/OldNameOfClass.php"    , "/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest/new/name/space/newClassName.php"), 
                        ("/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest/old/name/space/OldNameOfClassTest.php", "/Users/axelanconaesselmann/Dropbox/python/sublimePackages/phpRenameClass/phpRenameClassTest/replaceTest/new/name/space/newClassNameTest.php"),
                    ]
        self.assertEqual(expected, result)

    def test_namespaceAndClassFromFile(self):
        # Given a string containing a php class in a namespace
        string = """<?php
namespace a\\name\\spaced {
    /**
     * 
     */
    class NameOfAClass extends {

    }
}""" 
    
        # When namespaceAndClassFromFile is called
        result = phpRenameClass.namespaceAndClassFromFile(string)
        
        # Then returns the namespace and class name
        expected = "a\\name\\spaced\\", "NameOfAClass" 
        self.assertEqual(expected, result)
    
    

if __name__ == '__main__':
    unittest.main()