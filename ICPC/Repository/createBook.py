from typing import NamedTuple
import glob
import os
from pprint import pprint
import math

class Code(NamedTuple):
  name: str
  extension: str
  path: str
  order: int

# Only MacOS users, sorry :(
icpcPath = "/Users/*/*/ICPC/Codes/"
chaptersOrderName = "chaptersOrder.txt"
bookName = "Book.tex"
allCodesName = "allCodes.txt"

def write(file, str):
  file.write(str)

def writeln(file, str):
  file.write(str + '\n')

def special(str):
  ans = ""
  for ch in str:
    if ch == '\\' or ch == '\$' or ch == '\"' or ch == ' ':
      ans += '\\' # special dummy character
    ans += ch
  return ans

def endswith(x, suffixes):
  for suffix in suffixes:
    if x.lower().endswith(suffix.lower()):
      return True
  return False

def startswith(x, prefixes):
  for prefix in prefixes:
    if x.lower().startswith(prefix.lower()):
      return True
  return False
 
def getAllCodes(directory):
  ignore = set()
  allCodes = []
  order = dict()

  if os.path.isfile(allCodesName):
    # Get the order of the codes inside the book
    # Which codes we DON'T want in our book
    oldList = open(allCodesName, "r")
    for pos, line in enumerate(oldList.readlines()):
      line = line[:-1] # Remove endline
      if line.startswith("~"):
        line = line[1:] # Remove ~
        ignore.add(line) 

      order[line] = pos

  # Add any new code, it will appear at the beginning of the book (? 
  lastFileOrder = 0
  for path, directories, files in os.walk(directory):
    directories.sort()
    files.sort()

    if endswith(path, ["Tests", "Misc"]):
      continue

    for file in files:
      name, extension = os.path.splitext(file)

      if startswith(name, ["__latexindent_temp"]):
        continue

      if endswith(extension, [".cpp", ".h", ".txt", ".tex"]):
        fileOrder = order.get(name, -1)
        if fileOrder == -1:
          fileOrder = lastFileOrder

        allCodes.append(Code(name, extension, path, fileOrder))
        lastFileOrder = fileOrder

  # Sort codes by their position in allCodes.txt
  allCodes.sort(key = lambda code: code.order)

  # Generate a new list 
  newList = open("newList.txt", "a")
  alreadyWritten = set()
  for pos, code in enumerate(allCodes):
    if code.name not in alreadyWritten:
      writeln(newList, ("~" if code.name in ignore else "") + code.name)
      alreadyWritten.add(code.name)

    if pos + 1 < len(allCodes) and code.path != allCodes[pos + 1].path:
      writeln(newList, "")

  # Replace current list with the new list
  os.system(f"mv {newList.name} {allCodesName}")

  return [code for code in allCodes if code.name not in ignore]

def getChaptersOrder():
  chapters = open(chaptersOrderName, 'r')
  order = dict()
  for pos, chapter in enumerate(chapters.readlines()):
    order[chapter[:-1]] = pos
  return order

def getComplexity(code, pathToFile):
  text = ""
  if code.extension == ".tex":
    file = open(f"../{pathToFile}", "r").readlines()
    if file[0].startswith("\complexity"):
      # print(code.name, file[0])
      return file[0].replace("\n", "")
  return text

def toString(pathToFile, start = -math.inf, end = math.inf):
  text = ""
  file = open(f"../{pathToFile}", "r")
  for pos, line in enumerate(file.readlines()):
    if start <= pos and pos <= end:
      text += line
  return text

def writeBook(allCodes, bookName):
  chaptersOrder = getChaptersOrder()

  allCodes.sort(key = lambda code: [
    chaptersOrder.get(os.path.basename(code.path), -1), 
    code.order, 
    0 if code.extension in [".tex", ".txt"] else 1]
  )
  
  book = open(bookName, 'w')

  writeln(book, "\input{Preamble.tex}\n") 
  writeln(book, "\\begin{document}") 
  writeln(book, "  \\tableofcontents")
  writeln(book, "  % \\newpage")
  writeln(book, "  \input{Setup.tex}")

  chapter = ""
  for pos, code in enumerate(allCodes):
    chapterName = os.path.basename(code.path)
    
    if pos == 0 or (pos - 1 >= 0 and code.path != allCodes[pos - 1].path):
      # Create a new chapter 
      chapter = open(f"Chapters/{chapterName}.tex", 'w')
      # print(chapterName)
      writeln(book, f"  \input{{Chapters/{chapterName}.tex}}")
      writeln(chapter, f"\\nsection{{{chapterName}}}")

    path = code.path[code.path.find("Codes"):] + os.sep + code.name + code.extension

    complexity = getComplexity(code, path)
    if pos == 0 or (pos - 1 >= 0 and allCodes[pos - 1].name != code.name):
      writeln(chapter, f"\n\subsection{{{code.name} {complexity}}}")

    if endswith(code.extension, [".cpp", ".h"]):
      writeln(chapter, f"\\addcode{{../{path}}}")
    elif endswith(code.extension, [".txt", ".tex"]):
      if len(complexity) == 0:
        writeln(chapter, f"\input{{../{path}}}")
      else:
        # Until I find something better, I'll append all latex code :c
        write(chapter, toString(path, start = 1));
        
  writeln(book, "\end{document}") 
  return book.name

def updateChaptersOrder(bookName):
  book = open(bookName, 'r')
  chaptersOrder = open(chaptersOrderName, 'w')
  
  for chapter in book.readlines():
    chapter = chapter[:-6] # Remove .tex}\n from the back
    tmp = chapter.split("/")
    if len(tmp) == 2:
      writeln(chaptersOrder, tmp[1])

  chaptersOrder.close()

def main():
  icpc = glob.glob(icpcPath, recursive=True)[0]
  if os.path.isdir(icpc) == False:
    print("Wtf!, where is the ICPC repository?")
    return

  allCodes = getAllCodes(icpc)
  writeBook(allCodes, bookName)
  updateChaptersOrder(bookName)
  
  print("Book is ready!")

if __name__ == "__main__":
  main()