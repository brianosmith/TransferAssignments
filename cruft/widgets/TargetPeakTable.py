from ccpn.ui.gui.widgets.Table import Table


class TargetPeakTable(Table):

    columnDefs = [
        ('#', 'serial'),
        ('Assignment', 'assignment'),
        ('Distance', 'distance'),
    ]

    def populate(self, records):

        self.populateTable(
            rowObjects=records,
            columnDefs=self.columnDefs
        )