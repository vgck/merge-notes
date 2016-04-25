from aqt import mw
from aqt.browser import Browser
from aqt.utils import showInfo, tooltip
from aqt.qt import QDialogButtonBox, SIGNAL
from anki.hooks import wrap
from anki.utils import intTime

def mergeDupes(res):
    if not res:
        return

    # Loop through each duplicate
    for s, nidlist in res:
        note = mw.col.getNote(nidlist[0])

        # Create new note and copy all model fields from original note
        note_copy = mw.col.newNote()
        note_copy.fields = note.fields

        # Add the note to the database now to force anki to generate the cards
        note_copy.flush()
        mw.col.addNote(note_copy)

        # Set an initial state for the new cards
        for ncc, nc in zip(note_copy.cards(), note.cards()):
            mw.col.db.execute("update cards set mod=?, usn=?, type=?, queue=?, due=?, ivl=?, factor=?, reps=?, lapses=?, left=?, odue=0, odid=0 where id = ?",
                intTime(), mw.col.usn(), nc.type, nc.queue, nc.due, nc.ivl, nc.factor, nc.reps, nc.lapses, nc.left, ncc.id)

        # Loop through each duplicate note
        for nid in nidlist:
            n = mw.col.getNote(nid)
            note_copy.tags += n.tags

            # For each field that is unique and not blank, append to the new note
            for (name, value) in note_copy.items():
                arr = value.split(" / ")
                if (n[name] not in arr and n[name] != ""):
                    note_copy[name] = value + " / " + n[name]

            # Clone card scheduling
            for ncc, nc in zip(note_copy.cards(), n.cards()):
                if nc.ivl > ncc.ivl or nc.queue > ncc.queue:
                    mw.col.db.execute("update cards set mod=?, usn=?, type=?, queue=?, due=?, ivl=?, factor=?, reps=?, lapses=?, left=?, odue=0, odid=0 where id = ?",
                        intTime(), mw.col.usn(), nc.type, nc.queue, nc.due, nc.ivl, nc.factor, nc.reps, nc.lapses, nc.left, ncc.id)
        mw.col.remNotes(nidlist)

        # Refresh note
        note_copy.flush()

    # Reset collection and main window
    mw.col.reset()
    mw.reset()

    mw.progress.finish()

    tooltip(_("Notes merged."), period=1000)

def duplicatesReportWrap(self, web, fname, search, frm):
    res = self.mw.col.findDupes(fname, search)
    self._dupesButton2 = b2 = frm.buttonBox.addButton(
        _("Merge Duplicates"), QDialogButtonBox.ActionRole)
    self.connect(b2, SIGNAL("clicked()"), lambda: mergeDupes(res))

Browser.duplicatesReport = wrap(Browser.duplicatesReport, duplicatesReportWrap)