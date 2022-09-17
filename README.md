# chroma
A retargetable compiler heavily inspired by [colorForth](https://en.wikipedia.org/wiki/ColorForth). Work in progress! Development focusing on x86-64/Linux, with proof of concept support for other targets:

|Bits|Architecture|Platform/Board|Proof of Concept|
|-|-|-|-|
|8/16*|AVR|Arduino|🚧|
|16|x86-16|MSDOS|✔️|
|64|x86-64|Linux|✔️|

*natively 8-bit, 16-bit programming model

An eventual goal is to make the compiler self-hosting (i.e. written in chroma/colorForth itself). Currently this is only true for the core word macros. For this experimental development phase, the compilation is supported by a Python bootstrap compiler.

## Demo Applications

A couple sample apps working on both x86-16/DOS and x86-64/Linux targets
- to produce hexdumps from stdin
- to display the code with colouring using ANSI escape codes

![some sample code](/sample/sample.png)
![some sample code](/sample/sample2.png)

The colour printer app running on the DOS target, showing a listing of the source for the x86-64 target
![some sample code](/sample/sample3.png)

## colorForth
Colour is a core part of the language, it influences how words are to be interpreted and compiled. This is different to syntax highlighting in an editor which reflects the language, whereas here it add meaning. More about colorForth on [Wikipedia](https://en.wikipedia.org/wiki/ColorForth). 

## Colours
The colours being used now are similar as [in Chuck Moore's implementation](https://colorforth.github.io/parsed.html) with a few deviations. Not fixed/might change some aspects later.

|Colour|Semantics|
|-|-|
|White|Comment, ignored|
|Grey|Hex machine code -- compile directly into executable|
|Red|Beginning of a word definition: can jump or call to this location|
|Cyan|Beginning of a macro definition|
|Yellow|Compiler directive (executed directly in a word definition, executed on macro expansion*)|
|Green|Call or jump to a red definition|
|Purple|Variable declaration|

## Implementation
Serialisation: currently a letter corresponding to the colour switches the colour mode in a source file. A small compiler framework for testing is written in Python, with some parts also written in chroma/colorForth.
