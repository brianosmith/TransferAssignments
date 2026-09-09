from ccpn.ui.gui.widgets.Table import Table


class SourcePeakTable(Table):

    columnDefs = [
        ('#', 'serial'),
        ('Assignment', 'assignment'),
        ('Num Matches', 'numMatches'),
        ('Closest Distance', 'closestDistance'),
        ('Best Match', 'bestMatch'),
    ]

    def populate(self, records):

        self.populateTable(
            rowObjects=records,
            columnDefs=self.columnDefs
        )