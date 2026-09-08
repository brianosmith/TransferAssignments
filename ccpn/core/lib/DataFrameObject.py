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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-06-16 11:18:15 +0100 (Thu, June 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
import pyqtgraph as pg
from ccpn.ui.gui.widgets.Column import Column
from PyQt5 import QtCore, QtWidgets
from collections import OrderedDict
from ccpn.util.Logging import getLogger


DATAFRAME_OBJECT = '_object'
DATAFRAME_PID = 'Pid'
DATAFRAME_HASH = '#'
DATAFRAME_INDEX = 'Index'
DATAFRAME_ISDELETED = 'isDeleted'


class DataFrameObject(object):
    # class to handle pandas dataframe and matching object pid list
    def __init__(self, table=None, dataFrame=None, objectList=None, columnDefs=None):
        self._df = dataFrame
        # self._objectList = objectList
        self._objects = objectList.copy() if objectList else []
        # self._indexList = indexList
        self._columnDefinitions = columnDefs
        self._table = table

    @property
    def dataFrame(self):
        return self._df

    @dataFrame.setter
    def dataFrame(self, value=None):
        self._df = value

    @property
    def objects(self):
        return self._objects

    @property
    def numColumns(self):
        return self._columnDefinitions.numColumns

    @property
    def columnDefinitions(self):
        return self._columnDefinitions

    @columnDefinitions.setter
    def columnDefinitions(self, value=None):
        self._columnDefinitions = value

    @property
    def columns(self):
        return self._columnDefinitions.columns

    @property
    def visibleColumnHeadings(self):
        return [col for col in self._columnDefinitions.headings if col not in (self._table._hiddenColumns + self._table._internalColumns)]

    @property
    def userHeadings(self):
        return [col for col in self._columnDefinitions.headings if col not in (self._table._internalColumns)]

    @property
    def headings(self):
        return self._columnDefinitions.headings

    @property
    def setEditValues(self):
        return self._columnDefinitions.setEditValues

    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, value=None):
        self._table = value

    def find(self, table, text, column=DATAFRAME_PID, multiRow=False):
        model = table.model()

        # change column to correct index
        columns = list(range(table.columnCount()))
        columnNum = None
        for c in columns:
            colItem = table.horizontalHeaderItem(c)
            if colItem and column == colItem.text():
                columnNum = c
                break

        # search for 'text'
        if columnNum is not None:
            if multiRow:
                start = model.index(0, columnNum)
                matches = model.match(
                        start, QtCore.Qt.DisplayRole,
                        text, -1, QtCore.Qt.MatchExactly)
                return [mm.row() for mm in matches]

            else:
                start = model.index(0, columnNum)
                matches = model.match(
                        start, QtCore.Qt.DisplayRole,
                        text, 1, QtCore.Qt.MatchExactly)

                if matches:
                    return matches[0].row()

    def findObject(self, table, obj, column='_object'):
        """Return the row of the specified object
        """
        # change column to correct index
        columns = list(range(table.columnCount()))
        for c in columns:
            colItem = table.horizontalHeaderItem(c)
            if colItem and column == colItem.text():
                columnNum = c
                break
        else:
            return None

        foundObjs = [table.item(rr, columnNum).value for rr in range(table.rowCount())]
        if obj in foundObjs:
            return foundObjs.index(obj)

    def removeObject(self, obj):
        # remove an object from the class
        # row = self.find(self._table, str(obj.pid), column=DATAFRAME_PID)
        row = self.findObject(self._table, obj, column=DATAFRAME_OBJECT)
        if row is not None:
            self._table.silenceCallBack = True

            try:
                # remove from internal list
                self._objects.remove(obj)

                # remove from dataFrame by obj
                # self._df = self._df.ix[self._df[DATAFRAME_OBJECT] != obj]
                self._df = self._df.loc[self._df[DATAFRAME_OBJECT] != obj]

                # remove from table
                # # row = self.find(self._table, str(obj.pid), column=DATAFRAME_PID)
                # row = self.findObject(self._table, obj, column=DATAFRAME_OBJECT)
                # if row is not None:
                with self._table._guiTableUpdate(self):
                    self._table.removeRow(row)

            except Exception as es:
                getLogger().warning(str(es))
            finally:
                self._table.silenceCallBack = False

    def appendObject(self, obj, multipleAttr=None):
        # row = self.find(self._table, str(obj.pid), column=DATAFRAME_PID)
        row = self.findObject(self._table, obj, column=DATAFRAME_OBJECT)

        # check that the object doesn't already exist in the table
        if row is None:
            self._table.silenceCallBack = True

            try:
                # the object doesn't exist in list, so can be added
                listDict = OrderedDict()
                for header in self._columnDefinitions.columns:
                    try:
                        listDict[header.headerText] = header.getValue(obj)
                    except Exception as es:
                        getLogger().debug2(f'Error creating table information {es}')
                        listDict[header.headerText] = None

                if self._df.empty:
                    # need to create a new dataFrame, table with index of 0
                    # set the table and column headings

                    # set the initial objects; dataFrame needed to populate the first table
                    self._objects = [obj]
                    self._df = pd.DataFrame([listDict], columns=self.headings)

                    with self._table._guiTableUpdate(self):
                        self._table.setData(self._df.values)

                else:
                    # append a new line to the end

                    # set Index to next available - will change later
                    if not self._df.empty and DATAFRAME_INDEX in self._df:
                        newIndex = self._df[DATAFRAME_INDEX].max() + 1
                        if DATAFRAME_INDEX in listDict.keys():
                            listDict[DATAFRAME_INDEX] = newIndex

                    # update internal list
                    self._objects.append(obj)
                    appendDataFrame = pd.DataFrame([listDict], columns=self.headings)
                    # self._df = self._df.append(appendDataFrame)  # deprecated
                    self._df = pd.concat([self._df, appendDataFrame], ignore_index=True)

                    with self._table._guiTableUpdate(self):  # keep the column widths
                        self._table.appendRow(list(listDict.values()))

                    # # get indexing from pulldown selection and set in dataFrame/table
                    # # change to a finishing routine called updateTableIndexing when
                    # if multipleAttr:
                    #   newIndex = [multipleAttr.index(rr) for rr in self._objects]
                    #
                    #   objCol = indCol = None
                    #   for cc in range(self._table.columnCount()):
                    #     colName = self._table.horizontalHeaderItem(cc).text()
                    #     if colName == DATAFRAME_INDEX:
                    #       indCol = cc
                    #       print (DATAFRAME_INDEX, cc)
                    #     elif colName == DATAFRAME_OBJECT:
                    #       objCol = cc
                    #       print (DATAFRAME_OBJECT, cc)
                    #   if objCol and indCol:
                    #     print ('INDEXING')
                    #     print (multipleAttr)
                    #     for rr in range(self._table.rowCount()):
                    #
                    #       thisObj = self._table.item(rr, objCol).value
                    #       if thisObj in multipleAttr:
                    #         self._table.item(rr, indCol).setValue(multipleAttr.index(thisObj))

            except Exception as es:
                getLogger().warning(str(es))
            finally:
                self._table.silenceCallBack = False
                return True

    def renameObject(self, obj, oldPid):
        # row = self.find(self._table, str(oldPid), column=DATAFRAME_PID)
        # row = self.find(self._table, obj, column='_object')
        row = self.findObject(self._table, obj, column=DATAFRAME_OBJECT)
        if row is not None:
            self._table.silenceCallBack = True

            try:
                # generate a new row
                listDict = OrderedDict()
                for header in self._columnDefinitions.columns:
                    listDict[header.headerText] = header.getValue(obj)

                # self._df_foundPid = self._df.ix[self._df[DATAFRAME_OBJECT] == obj]
                # self._df = self._df.ix[self._df[DATAFRAME_OBJECT] != obj]
                self._df_foundPid = self._df.loc[self._df[DATAFRAME_OBJECT] == obj]
                self._df = self._df.loc[self._df[DATAFRAME_OBJECT] != obj]

                # keep the Index if it exists
                if not self._df_foundPid.empty and DATAFRAME_INDEX in self._df_foundPid:
                    newIndex = self._df_foundPid[DATAFRAME_INDEX].iloc[0]
                    if DATAFRAME_INDEX in listDict.keys():
                        listDict[DATAFRAME_INDEX] = newIndex

                # store to the table
                self._table.setRow(row, list(listDict.values()))

                # store the actual object in the dataFrame
                # if DATAFRAME_PID in listDict.keys():
                #   listDict[DATAFRAME_PID] = obj
                appendDataFrame = pd.DataFrame([listDict], columns=self.headings)
                # self._df = self._df.append(appendDataFrame)  # deprecated
                self._df = pd.concat([self._df, appendDataFrame], ignore_index=True)

            except Exception as es:
                getLogger().warning(str(es))
            finally:
                self._table.silenceCallBack = False
                return True

    def objAttr(self, headerText, obj):
        for header in self._columnDefinitions.columns:
            if header.headerText == headerText:
                return header.getValue(obj)

    def setObjAttr(self, headerText, obj, value):
        for header in self._columnDefinitions.columns:
            if header.headerText == headerText:
                header.setEditValue(obj, value)

    def changeObject(self, obj):
        # row = self.find(self._table, str(obj.pid), column=DATAFRAME_PID)
        row = self.findObject(self._table, obj, column=DATAFRAME_OBJECT)
        # _update = False
        if row is not None:
            self._table.silenceCallBack = True

            # try:

            # generate a new row
            listDict = OrderedDict()
            for header in self._columnDefinitions.columns:
                listDict[header.headerText] = header.getValue(obj)

            # self._df_foundPid = self._df.ix[self._df[DATAFRAME_OBJECT] == obj]
            # self._df = self._df.ix[self._df[DATAFRAME_OBJECT] != obj]
            self._df_foundPid = self._df.loc[self._df[DATAFRAME_OBJECT] == obj]
            self._df = self._df.loc[self._df[DATAFRAME_OBJECT] != obj]

            # keep the Index if it exists
            if not self._df_foundPid.empty and DATAFRAME_INDEX in self._df_foundPid:
                newIndex = self._df_foundPid[DATAFRAME_INDEX].iloc[0]
                if DATAFRAME_INDEX in listDict.keys():
                    listDict[DATAFRAME_INDEX] = newIndex

            # store to the table
            with self._table._guiTableUpdate(self):
                appendDataFrame = pd.DataFrame([listDict], columns=self.headings)
                # self._df = self._df.append(appendDataFrame)  # deprecated
                self._df = pd.concat([self._df, appendDataFrame], ignore_index=True)
                self._table.setRow(row, list(listDict.values()))

            # except Exception as es:
            #   getLogger().warning(str(es))
            # finally:
            self._table.silenceCallBack = False
            return True

        return False

    def objectExists(self, obj):
        return self.find(self._table, str(obj.pid), column=DATAFRAME_PID) is not None

    def emptyRow(self):
        """
        Create a blank row for populating undefined tables
        :return dict - based on headings:
        """
        headerDict = {}
        for h, header in enumerate(self._columnDefinitions.headings):
            headerDict[header] = h

        return headerDict
