# chroma
A retargetable compiler heavily inspired by [colorForth](https://en.wikipedia.org/wiki/ColorForth). Currently experimenting on different platforms with some very simple tests. Work in progress!

## Platforms

|Date|Bits|Architecture|Platform|Status|
|-|-|-|-|-|
|1974|8|8080/Z80|CP/M| ? |
|1981|16|x86|MSDOS| ✔️ proof of concept executable|
|1994|32|JVM|-| ⚠️ abandoned for now. Initial plan to 'exploit' [jsr/ret](https://docs.oracle.com/javase/specs/jvms/se17/html/jvms-6.html#jvms-6.5.jsr) instructions for word calls in a single method proved unworkable (difficulty in nesting, recursion etc). Want to return later to JVM as forth could map nicely to the stack machine. Native methods (called with `invokeXX`) work slightly different than words -- incompatible behaviour with stack frames/operand stack, and require method arguments/return types to be declared in the class file. Possible to emulate a return stack with an array and using switch tables, but a bit messy.|
|1996-|8|AVR|Embedded| ?|
|2003|64|x86|Linux| ? |
|2017|32/64|WebAssembly|Web| ? -- could map nicely as also a stack machine, though run into same issues as with JVM |

## Demo Applications
todo


## Taster
A small sample that compiles and runs on the MSDOS target. In a few sections, this defines:
- core x86/16-bit code generation macros
- implementation of language features (conditionals, loops) using this hardware
- set configuration of the COM binary output format
- a runtime with some useful words/functions
- usercode: printing some test patterns

![some sample code](/sample/sample.png)

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
