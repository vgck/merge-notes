from aqt import mw
from aqt.browser import Browser
from aqt.utils import showInfo, tooltip
from aqt.qt import QDialogButtonBox, SIGNAL
from anki.hooks import wrap
from anki.utils import intTime

def mergeDupes(res):
    if not res:
        return

    mw.checkpoint(_("Merge Duplicates"))
    
    def update(ncc, nc):
        mw.col.db.execute("update cards set mod=?, usn=?, type=?, queue=?, due=?, ivl=?, factor=?, reps=?, lapses=?, left=?, odue=0, odid=0 where id = ?",
            intTime(), mw.col.usn(), nc.type, nc.queue, nc.due, nc.ivl, nc.factor, nc.reps, nc.lapses, nc.left, ncc.id)

    for s, nidlist in res:
        note_copy = mw.col.newNote()
        for i, nid in enumerate(nidlist):
            n = mw.col.getNote(nid)
            note_copy.tags += n.tags

            # Add note to database now to force anki to generate cards, then copy an initial state for the new cards
            if (i == 0):
                note_copy.fields = n.fields
                mw.col.addNote(note_copy)
                for ncc, nc in zip(note_copy.cards(), n.cards()):
                    update(ncc, nc)

            for (name, value) in note_copy.items():
                arr = value.split(" / ")
                if (n[name] not in arr and n[name] != ""):
                    note_copy[name] = value + " / " + n[name]

            for ncc, nc in zip(note_copy.cards(), n.cards()):
                if nc.ivl > ncc.ivl or nc.queue > ncc.queue:
                    update(ncc, nc)
        mw.col.remNotes(nidlist)
        note_copy.flush()

    mw.progress.finish()
    mw.col.reset()
    mw.reset()
    tooltip(_("Notes merged."))

def onFindDupesWrap(self):
    self._dupesButton2 = None

def duplicatesReportWrap(self, web, fname, search, frm):
    res = self.mw.col.findDupes(fname, search)
    if not self._dupesButton2:
        self._dupesButton2 = b2 = frm.buttonBox.addButton(
            _("Merge Duplicates"), QDialogButtonBox.ActionRole)
        self.connect(b2, SIGNAL("clicked()"), lambda: mergeDupes(res))

Browser.onFindDupes = wrap(Browser.onFindDupes, onFindDupesWrap)
Browser.duplicatesReport = wrap(Browser.duplicatesReport, duplicatesReportWrap)