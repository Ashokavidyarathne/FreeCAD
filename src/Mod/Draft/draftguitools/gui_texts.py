# ***************************************************************************
# *   (c) 2009, 2010 Yorik van Havre <yorik@uncreated.net>                  *
# *   (c) 2009, 2010 Ken Cline <cline@frii.com>                             *
# *   (c) 2020 Eliud Cabrera Castillo <e.cabrera-castillo@tum.de>           *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************
"""Provides tools for creating text annotations with the Draft Workbench.

The textual block can consist of multiple lines.
"""
## @package gui_texts
# \ingroup DRAFT
# \brief Provides tools for creating text annotations with the Draft Workbench.

from PySide.QtCore import QT_TRANSLATE_NOOP
import sys

import FreeCAD as App
import FreeCADGui as Gui
import Draft_rc
import DraftVecUtils
import draftguitools.gui_base_original as gui_base_original
import draftguitools.gui_tool_utils as gui_tool_utils
from draftutils.translate import translate
from draftutils.messages import _msg

# The module is used to prevent complaints from code checkers (flake8)
True if Draft_rc.__name__ else False


class Text(gui_base_original.Creator):
    """Gui command for the Text tool."""

    def GetResources(self):
        """Set icon, menu and tooltip."""
        _tip = "Creates a multi-line annotation. CTRL to snap."

        return {'Pixmap': 'Draft_Text',
                'Accel': "T, E",
                'MenuText': QT_TRANSLATE_NOOP("Draft_Text", "Text"),
                'ToolTip': QT_TRANSLATE_NOOP("Draft_Text", _tip)}

    def Activated(self):
        """Execute when the command is called."""
        name = translate("draft", "Text")
        super(Text, self).Activated(name)
        if self.ui:
            self.dialog = None
            self.text = ''
            self.ui.sourceCmd = self
            self.ui.pointUi(name)
            self.call = self.view.addEventCallback("SoEvent", self.action)
            self.active = True
            self.ui.xValue.setFocus()
            self.ui.xValue.selectAll()
            _msg(translate("draft", "Pick location point"))
            Gui.draftToolBar.show()

    def finish(self, closed=False, cont=False):
        """Terminate the operation."""
        super(Text, self).finish(self)
        if self.ui:
            del self.dialog
            if self.ui.continueMode:
                self.Activated()

    def createObject(self):
        """Create the actual object in the current document."""
        txt = '['
        for line in self.text:
            if len(txt) > 1:
                txt += ', '
            if sys.version_info.major < 3:
                # Python2, string needs to be converted to unicode
                line = unicode(line)
                txt += '"' + str(line.encode("utf8")) + '"'
            else:
                # Python3, string is already unicode
                txt += '"' + line + '"'
        txt += ']'
        Gui.addModule("Draft")
        _cmd = 'Draft.makeText'
        _cmd += '('
        _cmd += txt + ', '
        _cmd += 'point=' + DraftVecUtils.toString(self.node[0])
        _cmd += ')'
        _cmd_list = ['text = ' + _cmd,
                     'Draft.autogroup(text)',
                     'FreeCAD.ActiveDocument.recompute()']
        self.commit(translate("draft", "Create Text"),
                    _cmd_list)
        self.finish(cont=True)

    def action(self, arg):
        """Handle the 3D scene events.

        This is installed as an EventCallback in the Inventor view.

        Parameters
        ----------
        arg: dict
            Dictionary with strings that indicates the type of event received
            from the 3D view.
        """
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event":  # mouse movement detection
            if self.active:
                (self.point,
                 ctrlPoint, info) = gui_tool_utils.getPoint(self, arg)
            gui_tool_utils.redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if arg["State"] == "DOWN" and arg["Button"] == "BUTTON1":
                if self.point:
                    self.active = False
                    Gui.Snapper.off()
                    self.node.append(self.point)
                    self.ui.textUi()
                    self.ui.textValue.setFocus()

    def numericInput(self, numx, numy, numz):
        """Validate the entry fields in the user interface.

        This function is called by the toolbar or taskpanel interface
        when valid x, y, and z have been entered in the input fields.
        """
        self.point = App.Vector(numx, numy, numz)
        self.node.append(self.point)
        self.ui.textUi()
        self.ui.textValue.setFocus()


Gui.addCommand('Draft_Text', Text())