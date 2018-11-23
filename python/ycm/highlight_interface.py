# Copyright (C) 2013-2018 YouCompleteMe contributors
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from future.utils import itervalues, iteritems
from collections import defaultdict
from ycm import vimsupport
import vim


class HighlightInterface( object ):
  def __init__( self, bufnr, user_options):
    self._bufnr = bufnr
    self._user_options = user_options
    self._highlights = []
    self._line_begins = {}
    self._line_ends   = {}

  def UpdateWithNewHighlights( self, highlights):
    #print("update buffer: "+str(self._bufnr)+", hl_num: "+str(len(highlights)))
    self._highlights = highlights

    with vimsupport.CurrentWindow():
      for window in vimsupport.GetWindowsForBufferNumber( self._bufnr ):
        vimsupport.SwitchWindow( window )

        # assign a unique_id for window, this should only be needed for the first window, do to
        # youcompleteme defered initialization
        if not window.vars.has_key('unique_id'):
          unique_id = vimsupport.GetIntValue("g:color_coded_unique_window_id")
          vim.command("let w:unique_id ={0}".format(unique_id))
          vim.command("let g:color_coded_unique_window_id += 1")

        # the highlight index of the window
        bufname = str(self._bufnr)+"."+str(window.vars['unique_id'])
        if not window.vars.has_key('color_code_name'):
          vim.command("let w:color_code_name=" +"\""+bufname+"\"")

        self._line_begins[bufname], self._line_ends[bufname] = vimsupport.GetLineRange(self._bufnr)

        # clear the old highlight
        vimsupport.ClearHighlightMatch(bufname);
        

        # apply new ones
        for highlight in highlights:
          line = highlight['line']
          if line>=self._line_begins[bufname] and line<=self._line_ends[bufname]:
            vimsupport.AddHighlightMatch(bufname, highlight['type'], line, highlight['col'], len(highlight['text']))
  
  def RefreshHighlights(self):
    # update with old highlights
    self.UpdateWithNewHighlights(self._highlights)
  
  def ClearCurrentWindowHighlights(self):
    window = vimsupport.GetCurrentWindow()
    bufname = str(self._bufnr)+"."+str(window.vars['unique_id'])
    vimsupport.ClearHighlightMatch(bufname);

  def MoveHighlight(self, start, end):
    window = vimsupport.GetCurrentWindow()

    # assign a unique_id for window, this should only be needed for the first window, do to
    # youcompleteme defered initialization
    if not window.vars.has_key('unique_id'):
      unique_id = vimsupport.GetIntValue("g:color_coded_unique_window_id")
      vim.command("let w:unique_id ={0}".format(unique_id))
      vim.command("let g:color_coded_unique_window_id += 1")

    # the highlight index of the window
    bufname = str(self._bufnr)+"."+str(window.vars['unique_id'])
    if not window.vars.has_key('color_code_name'):
      vim.command("let w:color_code_name=" +"\""+bufname+"\"")

    # record the new line range
    [self._line_begins[bufname], self._line_ends[bufname]] = [start, end];

    #remove the old ones
    vimsupport.ClearHighlightMatch(bufname);

    # apply new ones
    for highlight in self._highlights:
      line = highlight['line']
      # only apply ones between line_begin and line_end
      if line >=self._line_begins[bufname] and line<=self._line_ends[bufname]:
        vimsupport.AddHighlightMatch(bufname, highlight['type'], line, highlight['col'], len(highlight['text']))
