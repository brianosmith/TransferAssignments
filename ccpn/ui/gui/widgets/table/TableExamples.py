"""
Few Examples of how to build a Table Widgets
"""

import pandas as pd

def _initTestApplication():
    """
    Create a Test Application
    """
    from ccpn.ui.gui.widgets.Application import TestApplication
    testApplication = TestApplication()
    return testApplication


def _buildLayout(testApplication, table):
    """
    Create a  layout to display the table
    :param: table:  the Table object to display
    """
    from PyQt5 import QtWidgets
    win = QtWidgets.QMainWindow()
    frame = QtWidgets.QFrame()
    layout = QtWidgets.QGridLayout()
    frame.setLayout(layout)
    win.setCentralWidget(frame)
    frame.layout().addWidget(table, 0, 0)
    win.setWindowTitle(f'Example {table.__class__.__name__}')
    win.show()
    testApplication.start()

def simplestTable():
    """ Build the simplest table possible"""
    from ccpn.ui.gui.widgets.table.Table import Table
    # must create an app for this example to work.
    _testApp = _initTestApplication()

    # create a dataFrame
    df = pd.DataFrame(
                                {'Cars': ['BMW', 'AUDI'],
                                 'Colours':['Red', 'Green']}
                                 )

    # init the table
    table = Table(None, df=df,)

    # Add to a layout if not given a grid and a parent layout to TableABC
    _buildLayout(_testApp, table)

def _selectionCallback(*args, **kwargs):
    print('Selected', args)

def customPandasTable():
    """ Build the simplest table possible"""
    from ccpn.ui.gui.widgets.table.CustomPandasTable import CustomDataFrameTable
    from ccpn.ui.gui.widgets.Column import Column
    # must create an app for this example to work.
    _testApp = _initTestApplication()

    # create a dataFrame
    df = pd.DataFrame(
                                {
                            'Cars': ['BMW', 'AUDI'],
                            # 'Velocity_': [122, 144],
                             'Colours':['Red', 'Green'],
                            #  'year': ['1999', '2000'],
                            # 'Symbol': ['B', 'A'],
                                 }
                                 )

    # init the table
    _columns = [
        Column('Vehicle', 'Cars', rawDataHeading='Cars', tipText='CarsCars ', isHidden=False),
        Column('Tint', 'Colours', rawDataHeading='Colours', tipText='ColoursColoursColours ', isInternal=True),
        Column('Speed', 'Velocity', rawDataHeading='Velocity', tipText='VelocityVelocity ', isInternal=True),
        # Column('Symbol', 'Symbol', tipText='Symbol '),

    ]

    table = CustomDataFrameTable(None, dataFrame=df, columns=_columns
                                 ,selectionCallback=_selectionCallback)


    # Add to a layout if not given a grid and a parent layout to TableABC
    _buildLayout(_testApp, table)

# simplestTable()
customPandasTable()

