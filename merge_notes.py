# import the main window object (mw) from ankiqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *
# import hooks
from anki.hooks import addHook
from anki.hooks import wrap
# import browser
from aqt.browser import Browser


import sre_constants
import cgi
import time
import re
from operator import  itemgetter
from anki.lang import ngettext

from aqt.qt import *
import anki
import aqt.forms
from anki.utils import fmtTimeSpan, ids2str, stripHTMLMedia, isWin, intTime, isMac
from aqt.utils import saveGeom, restoreGeom, saveSplitter, restoreSplitter, \
    saveHeader, restoreHeader, saveState, restoreState, applyStyles, getTag, \
    showInfo, askUser, tooltip, openHelp, showWarning, shortcut, getBase, mungeQA
from anki.hooks import runHook, addHook, remHook
from aqt.webview import AnkiWebView
from aqt.toolbar import Toolbar
from anki.consts import *
from anki.sound import playFromText, clearAudioQueue

def onFindDupes2(self):
    d = QDialog(self)
    frm = aqt.forms.finddupes.Ui_Dialog()
    frm.setupUi(d)
    restoreGeom(d, "findDupes")
    fields = sorted(anki.find.fieldNames(self.col, downcase=False))
    frm.fields.addItems(fields)
    self._dupesButton = None
    self._dupesButton2 = None
    # links
    frm.webView.page().setLinkDelegationPolicy(
        QWebPage.DelegateAllLinks)
    self.connect(frm.webView,
                 SIGNAL("linkClicked(QUrl)"),
                 self.dupeLinkClicked)
    def onFin(code):
        saveGeom(d, "findDupes")
    self.connect(d, SIGNAL("finished(int)"), onFin)
    def onClick():
        field = fields[frm.fields.currentIndex()]
        self.duplicatesReport(frm.webView, field, frm.search.text(), frm)
    search = frm.buttonBox.addButton(
        _("Search"), QDialogButtonBox.ActionRole)
    self.connect(search, SIGNAL("clicked()"), onClick)
    d.show()

def mergeDupes(res):
    if not res:
        return

    # Loop through each duplicate
    for s, nidlist in res:
        note = mw.col.getNote(nidlist[0])
        model = note._model

        # Create new note and copy all model fields from original note
        note_copy = mw.col.newNote()
        note_copy.fields = note.fields

        # Loop through each duplicate note
        for nid in nidlist:
            n = mw.col.getNote(nid)
            # For each field that is unique and not blank, append to the new note
            for (name, value) in note_copy.items():
                arr = value.split(" / ")
                if (n[name] not in arr and n[name] != ""):
                    note_copy[name] = value + " / " + n[name]
            note_copy.tags += n.tags
        mw.col.remNotes(nidlist)

        # Refresh note and add to database
        note_copy.flush()
        mw.col.addNote(note_copy)

    # Reset collection and main window
    mw.col.reset()
    mw.reset()

    mw.progress.finish()

    tooltip(_("Notes merged."), period=1000)

def duplicatesReport2(self, web, fname, search, frm):
    self.mw.progress.start()
    res = self.mw.col.findDupes(fname, search)
    if not self._dupesButton:
        self._dupesButton = b = frm.buttonBox.addButton(
            _("Tag Duplicates"), QDialogButtonBox.ActionRole)
        self.connect(b, SIGNAL("clicked()"), lambda: self._onTagDupes(res))
    if not self._dupesButton2:
        self._dupesButton2 = b2 = frm.buttonBox.addButton(
            _("Merge Duplicates"), QDialogButtonBox.ActionRole)
        self.connect(b2, SIGNAL("clicked()"), lambda: mergeDupes(res))
    t = "<html><body>"
    groups = len(res)
    notes = sum(len(r[1]) for r in res)
    part1 = ngettext("%d group", "%d groups", groups) % groups
    part2 = ngettext("%d note", "%d notes", notes) % notes
    t += _("Found %(a)s across %(b)s.") % dict(a=part1, b=part2)
    t += "<p><ol>"
    for val, nids in res:
        t += '<li><a href="%s">%s</a>: %s</a>' % (
            "nid:" + ",".join(str(id) for id in nids),
            ngettext("%d note", "%d notes", len(nids)) % len(nids),
            cgi.escape(val))
    t += "</ol>"
    t += "</body></html>"
    web.setHtml(t)
    self.mw.progress.finish()

Browser.onFindDupes = onFindDupes2
Browser.duplicatesReport = duplicatesReport2
