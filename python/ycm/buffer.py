# Copyright (C) 2016, Davit Samvelyan
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

import vim
from ycm import vimsupport
from ycm.client.event_notification import EventNotification
from ycm.diagnostic_interface import DiagnosticInterface
from ycm.highlight_interface import HighlightInterface

HIGHLIGHT_UI_FILETYPES = {'cpp', 'c'}

DIAGNOSTIC_UI_FILETYPES = { 'cpp', 'cs', 'c', 'objc', 'objcpp', 'cuda',
                            'javascript', 'typescript' }
DIAGNOSTIC_UI_ASYNC_FILETYPES = { 'java' }


# Emulates Vim buffer
# Used to store buffer related information like diagnostics, latest parse
# request. Stores buffer change tick at the parse request moment, allowing
# to effectively determine whether reparse is needed for the buffer.
class Buffer( object ):

  def __init__( self, bufnr, user_options, async_diags ):
    self.number = bufnr
    self._parse_tick = 0
    self._handled_tick = 0
    self._parse_request = None
    self._parse_request_buf = None
    self._async_diags = async_diags
    self._diag_interface = DiagnosticInterface( bufnr, user_options )
    self._hl_interface = HighlightInterface(bufnr, user_options )

  def FileParseRequestReady( self, block = False ):
    if not self._parse_request:
      return 0
    elif block:
      return 1
    elif self._parse_request.Done():
      if self._parse_request_buf:
        return 1
      else:
        return 2

    return bool( self._parse_request and
                 ( block or self._parse_request.Done() ) )


  def SendParseRequest( self, extra_data ):
    if self._parse_request==None:
      self._parse_request = EventNotification( 'FileReadyToParse',
                                               extra_data = extra_data )
      self._parse_request.Start()
      #print("send request")
      # Decrement handled tick to ensure correct handling when we are forcing
      # reparse on buffer visit and changed tick remains the same.
      self._handled_tick -= 1
      self._parse_tick = self._ChangedTick()
    else:
      # buf this request
      #print("buf request")
      self._parse_request_buf = EventNotification('FileReadyToParse',
                                               extra_data = extra_data)

  def TrySendBufRequest(self):
    if self._parse_request_buf:
      self._parse_request = self._parse_request_buf
      self._parse_request_buf = None
      self._parse_request.Start()
      #print("send buf request")
      self._handled_tick -= 1
      self._parse_tick = self._ChangedTick()


  def NeedsReparse( self ):
    return self._parse_tick != self._ChangedTick()


  def ShouldResendParseRequest( self ):
    return bool( self._parse_request and self._parse_request.ShouldResend() )


  def UpdateDiagnostics( self, force=False ):
    if force or not self._async_diags:
      response = self._parse_request.Response();
      diagnostics = [];
      if isinstance(response, list):
        diagnostics = response
      elif isinstance(response, dict):
        diagnostics = response["diagnostics"]
      self.UpdateWithNewDiagnostics( diagnostics )
    else:
      # We need to call the response method, because it might throw an exception
      # or require extra config confirmation, even if we don't actually use the
      # diagnostics.
      self._parse_request.Response()
  

  def UpdateHighlights(self):
    response = self._parse_request.Response();
    highlights = []
    if isinstance(response, dict):
      highlights = response['highlights']

    self.UpdateWithNewHighlights(highlights)
  

  def UpdateWithNewHighlights(self, highlights):
    self._hl_interface.UpdateWithNewHighlights( highlights )

  
  def MoveHighlight(self, start, end):
    self._hl_interface.MoveHighlight(start, end)


  def RefreshHighlights(self):
    self._hl_interface.RefreshHighlights()


  def ClearCurrentWindowSemanticHighlight(self):
    self._hl_interface.ClearCurrentWindowHighlights()


  def UpdateWithNewDiagnostics( self, diagnostics ):
    self._diag_interface.UpdateWithNewDiagnostics( diagnostics )


  def UpdateMatches( self ):
    self._diag_interface.UpdateMatches()


  def PopulateLocationList( self ):
    return self._diag_interface.PopulateLocationList()


  def GetResponse( self ):
    return self._parse_request.Response()


  def IsResponseHandled( self ):
    return self._handled_tick == self._parse_tick


  def MarkResponseHandled( self ):
    self._parse_request = None
    self._handled_tick = self._parse_tick


  def OnCursorMoved( self ):
    self._diag_interface.OnCursorMoved()


  def GetErrorCount( self ):
    return self._diag_interface.GetErrorCount()


  def GetWarningCount( self ):
    return self._diag_interface.GetWarningCount()


  def _ChangedTick( self ):
    return vimsupport.GetBufferChangedTick( self.number )


class BufferDict( dict ):

  def __init__( self, user_options ):
    self._user_options = user_options


  def __missing__( self, key ):
    # Python does not allow to return assignment operation result directly
    new_value = self[ key ] = Buffer(
      key,
      self._user_options,
      any( x in DIAGNOSTIC_UI_ASYNC_FILETYPES
           for x in vimsupport.GetBufferFiletypes( key ) ) )

    return new_value
