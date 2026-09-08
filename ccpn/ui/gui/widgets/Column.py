"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-11-30 11:22:07 +0000 (Wed, November 30, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtCore, QtWidgets
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.util.Logging import getLogger


BG_COLOR = QtGui.QColor('#E0E0E0')

COLUMN_COLNAME = 'colName'
COLUMN_FUNC = 'func'
COLUMN_TIPTEXT = 'tipText'
COLUMN_SETEDITVALUE = 'setEditValue'
COLUMN_FORMAT = 'format'
COLUMN_COLDEFS = [COLUMN_COLNAME, COLUMN_FUNC, COLUMN_TIPTEXT, COLUMN_SETEDITVALUE, COLUMN_FORMAT]


# TODO:ED add some documentation here
class ColumnClass:
    def __init__(self, columnList):
        # ERROR checking for columnList. All of this as to be changed asap with a dict style and pass the kwargs and not rely on a tuple or tuple
        columnList_ = []
        for i in columnList:
            if isinstance(i, tuple):
                if len(i) != len(COLUMN_COLDEFS):
                    missing = len(COLUMN_COLDEFS) - len(i)
                    i += (None,) * missing  # this is still a bad fix!
                columnList_.append(i)

        self._columns = [Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat) for
                         colName, func, tipText, editValue, columnFormat in columnList_]  # FIXME . this mechanism is very fragile

    def addColumn(self, newColumn):
        columnToAdd = [Column(colName, func, tipText=tipText, setEditValue=editValue, format=columnFormat) for
                       colName, func, tipText, editValue, columnFormat in newColumn]

        if self._columns:
            self._columns.append(columnToAdd)
        else:
            self._columns = columnToAdd

    def setColumns(self, columns):
        """
        :param columns:  list of Column objects
        :return:  None
        """
        self._columns = columns

    @property
    def numColumns(self):
        if self._columns:
            return len(self._columns)
        else:
            return None

    @property
    def columns(self):
        return self._columns

    @property
    def headings(self):
        return [heading.headerText for heading in self._columns]

    @property
    def functions(self):
        return [heading.getValue for heading in self._columns]

    @property
    def tipTexts(self):
        return [heading.tipText for heading in self._columns]

    @property
    def getEditValues(self):
        return [heading.getValue for heading in self._columns]

    @property
    def setEditValues(self):
        return [heading.setEditValue for heading in self._columns]

    @property
    def formats(self):
        return [heading.format for heading in self._columns]


# TODO:ED add some documentation here

class Column:

    def __init__(self, headerText, getValue, getEditValue=None, setEditValue=None,
                 editClass=None, editArgs=None, editKw=None, tipText=None,
                 getColor=None, getIcon=None, stretch=False, format=None,
                 editDecimals=None, editStep=None, rawDataHeading=None,
                 isHidden = False, isInternal = False, columnWidth=None,
                 alignment=QtCore.Qt.AlignCenter, **kwargs):
        # editDecimals=None, editStep=None, alignment=QtCore.Qt.AlignLeft,
        # orderFunc=None):

        self.headerText = headerText
        self.getValue = getValue or self._defaultText
        self.getEditValue = getEditValue or getValue
        self.setEditValue = setEditValue
        self.editClass = editClass
        self.editArgs = editArgs or []
        self.editKw = editKw or {}
        self.stretch = stretch
        self.format = format
        self.editDecimals = editDecimals
        self.editStep = editStep
        self.defaultIcon = None
        self.rawDataHeading = rawDataHeading
        if isinstance(getValue, str) and rawDataHeading is None:
            self.rawDataHeading = getValue
        self.isHidden = isHidden
        self.isInternal = isInternal
        self.columnWidth = columnWidth
        #self.alignment = ALIGN_OPTS.get(alignment, alignment) | Qt.AlignVCenter
        # Alignment combinations broken in PyQt4 v1.1.1
        # Use better default than top left
        self.alignment = alignment
        # self.orderFunc = orderFunc
        self.heading = kwargs.get('heading', self.headerText)


        self.getIcon = getIcon #or self._defaultIcon
        self.getColor = getColor #or self._defaultColor
        self.tipText = tipText

        self._checkTextAttrs()

    @property
    def heading(self):
        """back-compatibility only """
        return self.headerText

    @heading.setter
    def heading(self, heading):
        """back-compatibility only """
        self.headerText = heading

    def orderFunc(self, objA, objB):
        return (universalSortKey(self.getValue(objA)) < universalSortKey(self.getValue(objB)))

    def getFormatValue(self, obj):

        value = self.getValue(obj)
        format = self.format
        if format and (value is not None):
            return format % value
        else:
            return value

    def _checkTextAttrs(self):

        if isinstance(self.getValue, str):
            attr = self.getValue
            self.getValue = lambda obj: getattr(obj, attr)

        if isinstance(self.getEditValue, str):
            attr = self.getEditValue
            self.getEditValue = lambda obj: getattr(obj, attr)

        if isinstance(self.setEditValue, str):
            attr = self.setEditValue
            self.setEditValue = lambda obj, value: setattr(obj, attr, value)

        if isinstance(self.getIcon, QtGui.QIcon):
            self.defaultIcon = self.getIcon
            self.getIcon = self._defaultIcon

    def _defaultText(self, obj):

        return ' '

    def _defaultColor(self, obj):

        return BG_COLOR

    def _defaultIcon(self, obj):

        return self.defaultIcon
