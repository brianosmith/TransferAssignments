# TransferAssignments
CCPN V3 plugin to replicate V2 Copy Peak Assignments workflow

See https://sites.google.com/site/ccpnwiki/home/documentation/ccpnmr-analysis/popup-reference/assignment-copy-assignments 
for the inspiration although not all features have been re-implemented.
Contact Brian dot Smith art glasgow.ac.uk with any bug reports or feature requests.

## To install as a user plugin
Copy the ccpn/plugins/TransferAssignments directory/folder to a destination
that it can be found in - usually <path to user's home>/.ccpn/plugins by default.
Then start/restart your AnalysisAssign session and it should appear under the 
Plugins->User Plugins menu.

## To install as a plugin for all users
Copy the ccpn/plugins/TransferAssignments directory/folder to the src/python/ccpn/plugins
of your installation and start/restart your AnalysisAssign session and it should appear
under the Plugins->CCPN Plugins menu

## Notes
- The module layout works best when docked to the full height of your main window
or popped out and resized to a tall aspect ratio.
- Settings are available via the settings cog.
- The module should work on any nDimensional peak lists but has only been tested on 2Ds
so far. There's no support (yet) for disambiguating which axes should be matched if you have
dimensions with matching isotopeCodes in either source or target spectrum.
- Scales are used in the calculation < distance = sqrt(((x1-x2)*scale factor in x)^2 + ((y1-y2)*scale factor in y)^2) >
i.e. smaller number -> lower weighting for that dimension
- 