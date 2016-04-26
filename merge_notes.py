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
        #if not mw.col.decks.current()['dyn']:
        #    curdid = mw.col.decks.current()['id']
        #else:
        curdid = nc.did
        mw.col.db.execute("update cards set did=?, mod=?, usn=?, type=?, queue=?, due=?, ivl=?, factor=?, reps=?, lapses=?, left=?, odue=0, odid=0 where id = ?",
            curdid, intTime(), mw.col.usn(), nc.type, nc.queue, nc.due, nc.ivl, nc.factor, nc.reps, nc.lapses, nc.left, ncc.id)

    for s, nidlist in res:
        note_copy = mw.col.newNote()
        for i, nid in enumerate(nidlist):
            n = mw.col.getNote(nid)
            note_copy.tags += n.tags

            # Because apparently it's nontrivial to retrive cards by ord# so force all cards to exist before we copy the scheduling
            for (name, value) in n.items():
                if not n[name]:
                    n[name] = "BLANK"
            n.flush()

            # Add note to database now to force anki to generate cards, then copy an initial state for the new cards
            if (i == 0):
                note_copy.fields = n.fields
                mw.col.addNote(note_copy)
                for ncc, nc in zip(note_copy.cards(), n.cards()):
                    update(ncc, nc)

            for (name, value) in note_copy.items():
                if value == "BLANK":
                    note_copy[name] = ""
                if n[name] != "BLANK":
                    if not value or value == "BLANK":
                        note_copy[name] = n[name]
                        continue
                    arr = value.split(" / ")
                    if (n[name] not in arr):
                        note_copy[name] = value + " / " + n[name]

            for ncc, nc in zip(note_copy.cards(), n.cards()):
                if nc.ivl > ncc.ivl or nc.queue > ncc.queue:
                    update(ncc, nc)
        note_copy.flush()
        mw.col.remNotes(nidlist)
        mw.col.tags.bulkRem([note_copy.id], _("duplicate"))

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