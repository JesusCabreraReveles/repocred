# VHS script for the RepoCred demo GIF.
# Install vhs (https://github.com/charmbracelet/vhs), then run:  vhs examples/demo.tape
# Output: examples/demo.gif

Output examples/demo.gif

Set FontSize 18
Set Width 1100
Set Height 760
Set Padding 24
Set Theme "Dracula"

Type "repocred score . --audit"
Sleep 600ms
Enter
Sleep 4s
