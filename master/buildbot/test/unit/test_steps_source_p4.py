# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members
# Portions Copyright 2013 Bad Dog Consulting


from twisted.trial import unittest
from buildbot.steps.source.p4 import P4
from buildbot.status.results import SUCCESS
from buildbot.test.util import sourcesteps
from buildbot.test.util.properties import ConstantRenderable
from buildbot.test.fake.remotecommand import ExpectShell, Expect
from buildbot import config
import textwrap


class TestP4(sourcesteps.SourceStepMixin, unittest.TestCase):

    def setUp(self):
        return self.setUpSourceStep()

    def tearDown(self):
        return self.tearDownSourceStep()

    def setupStep(self, step, args={}, patch=None, **kwargs):
        step = sourcesteps.SourceStepMixin.setupStep(self, step, args={}, patch=None, **kwargs)
        self.build.getSourceStamp().revision = args.get('revision', None)

        # builddir propety used to create absolute path required in perforce client spec.
        self.properties.setProperty('builddir', '/home/user/workspace', 'P4')

    def test_no_empty_step_config(self):
        self.assertRaises(config.ConfigErrors, lambda: P4())

    def test_no_multiple_type_step_config(self):
        self.assertRaises(config.ConfigErrors, lambda:
                          P4(p4viewspec=('//depot/trunk', ''),
                             p4base='//depot', p4branch='trunk',
                             p4extra_views=['src', 'doc']))

    def test_no_p4viewspec_is_string_step_config(self):
        self.assertRaises(config.ConfigErrors, lambda:
                          P4(p4viewspec='a_bad_idea'))

    def test_no_p4base_has_trailing_slash_step_config(self):
        self.assertRaises(config.ConfigErrors, lambda:
                          P4(p4base='//depot/'))

    def test_no_p4branch_has_trailing_slash_step_config(self):
        self.assertRaises(config.ConfigErrors, lambda:
                          P4(p4base='//depot', p4branch='blah/'))

    def test_no_p4branch_with_no_p4base_step_config(self):
        self.assertRaises(config.ConfigErrors, lambda:
                          P4(p4branch='blah'))

    def test_no_p4extra_views_with_no_p4base_step_config(self):
        self.assertRaises(config.ConfigErrors, lambda:
                          P4(p4extra_views='blah'))

    def test_incorrect_mode(self):
        self.assertRaises(config.ConfigErrors, lambda:
                          P4(p4base='//depot',
                             mode='invalid'))

    def test_mode_incremental_p4base_with_revision(self):
        self.setupStep(P4(p4port='localhost:12000', mode='incremental',
                          p4base='//depot', p4branch='trunk',
                          p4user='user', p4client='p4_client1', p4passwd='pass'),
                       dict(revision='100',))

        client_spec = textwrap.dedent('''\
        Client: p4_client1

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/trunk/... //p4_client1/...
        ''');

        self.expectCommands(
            ExpectShell(workdir='wkdir',  # defaults to this, only changes if it has a copy mode.
                        command=['p4', '-V'])  # expected remote command
            + 0,  # expected exit status

            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', 'user',
                                       '-P', 'pass', '-c', 'p4_client1',
                                       'client', '-i'],
                        initialStdin=client_spec)
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', 'user',
                                       '-P', 'pass', '-c', 'p4_client1',
                                       'sync', '//depot...@100'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', 'user',
                                       '-P', 'pass', '-c', 'p4_client1',
                                       'changes', '-m1', '#have'])
            + ExpectShell.log('stdio',
                              stdout="Change 100 on 2013/03/21 by user@machine \'duh\'")
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        self.expectProperty('got_revision', '100', 'P4')
        return self.runStep()

    def _incremental(self, client_stdin=''):
        self.expectCommands(
            ExpectShell(workdir='wkdir',  # defaults to this, only changes if it has a copy mode.
                        command=['p4', '-V'])  # expected remote command
            + 0,  # expected exit status

            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', 'user',
                                       '-P', 'pass', '-c', 'p4_client1',
                                       'client', '-i'],
                        initialStdin=client_stdin,)
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', 'user',
                                       '-P', 'pass', '-c', 'p4_client1',
                                       'sync'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', 'user',
                                       '-P', 'pass', '-c', 'p4_client1',
                                       'changes', '-m1', '#have'])
            + ExpectShell.log('stdio',
                              stdout="Change 100 on 2013/03/21 by user@machine \'duh\'")
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        self.expectProperty('got_revision', '100', 'P4')
        return self.runStep()

    def test_mode_incremental_p4base(self):
        self.setupStep(P4(p4port='localhost:12000', mode='incremental',
                          p4base='//depot', p4branch='trunk',
                          p4user='user', p4client='p4_client1', p4passwd='pass'))

        client_spec = textwrap.dedent('''\
        Client: p4_client1

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/trunk/... //p4_client1/...
        ''')
        self._incremental(client_stdin=client_spec)

    def test_mode_incremental_p4base_with_p4extra_views(self):
        self.setupStep(P4(p4port='localhost:12000', mode='incremental',
                          p4base='//depot', p4branch='trunk',
                          p4extra_views=[('-//depot/trunk/test', 'test'),
                                         ('-//depot/trunk/doc', 'doc')],
                          p4user='user', p4client='p4_client1', p4passwd='pass'))
        client_spec = textwrap.dedent('''\
        Client: p4_client1

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/trunk/... //p4_client1/...
        \t-//depot/trunk/test/... //p4_client1/test/...
        \t-//depot/trunk/doc/... //p4_client1/doc/...
        ''')
        self._incremental(client_stdin=client_spec)

    def test_mode_incremental_p4viewspec(self):
        self.setupStep(P4(p4port='localhost:12000', mode='incremental',
                          p4viewspec=[('//depot/trunk/', '')],
                          p4user='user', p4client='p4_client1', p4passwd='pass'))
        client_spec = textwrap.dedent('''\
        Client: p4_client1

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/trunk/... //p4_client1/...
        ''')
        self._incremental(client_stdin=client_spec)

    def _full(self, client_stdin='', p4client='p4_client1', p4user='user'):
        self.expectCommands(
            ExpectShell(workdir='wkdir',  # defaults to this, only changes if it has a copy mode.
                        command=['p4', '-V'])  # expected remote command
            + 0,  # expected exit status

            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', p4user,
                                       '-P', 'pass', '-c', p4client, 'client',
                                       '-i'],
                        initialStdin=client_stdin)
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', p4user,
                                       '-P', 'pass', '-c', p4client, 'sync',
                                       '#none'])
            + 0,

            Expect('rmdir', {'dir': 'wkdir', 'logEnviron': True})
            + 0,

            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', p4user,
                                       '-P', 'pass', '-c', p4client, 'sync'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['p4', '-p', 'localhost:12000', '-u', p4user,
                                       '-P', 'pass', '-c', p4client, 'changes',
                                       '-m1', '#have'])
            + ExpectShell.log('stdio',
                              stdout="Change 100 on 2013/03/21 by user@machine \'duh\'")
            + 0,
        )
        self.expectOutcome(result=SUCCESS, status_text=["update"])
        self.expectProperty('got_revision', '100', 'P4')
        return self.runStep()

    def test_mode_full_p4base(self):
        self.setupStep(
            P4(p4port='localhost:12000',
               mode='full', p4base='//depot', p4branch='trunk',
               p4user='user', p4client='p4_client1', p4passwd='pass'))

        client_stdin = textwrap.dedent('''\
        Client: p4_client1

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/trunk/... //p4_client1/...\n''')
        self._full(client_stdin=client_stdin)

    def test_mode_full_p4viewspec(self):
        self.setupStep(
            P4(p4port='localhost:12000',
               mode='full', p4viewspec=[('//depot/main/', '')],
               p4user='user', p4client='p4_client1', p4passwd='pass'))
        client_stdin = textwrap.dedent('''\
        Client: p4_client1

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/main/... //p4_client1/...\n''')

        self._full(client_stdin=client_stdin)

    def test_mode_full_renderable_p4base(self):
        # Note that the config check skips checking p4base if it's a renderable
        self.setupStep(
            P4(p4port='localhost:12000',
               mode='full', p4base=ConstantRenderable('//depot'),
               p4branch='release/1.0', p4user='user', p4client='p4_client2',
               p4passwd='pass'))

        client_stdin = textwrap.dedent('''\
        Client: p4_client2

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/release/1.0/... //p4_client2/...\n''')

        self._full(client_stdin=client_stdin, p4client='p4_client2')

    def test_mode_full_renderable_p4client(self):
        # Note that the config check skips checking p4base if it's a renderable
        self.setupStep(
            P4(p4port='localhost:12000',
               mode='full', p4base='//depot', p4branch='trunk',
               p4user='user', p4client=ConstantRenderable('p4_client_render'),
               p4passwd='pass'))

        client_stdin = textwrap.dedent('''\
        Client: p4_client_render

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/trunk/... //p4_client_render/...\n''')

        self._full(client_stdin=client_stdin, p4client='p4_client_render')

    def test_mode_full_renderable_p4branch(self):
        # Note that the config check skips checking p4base if it's a renderable
        self.setupStep(
            P4(p4port='localhost:12000',
               mode='full', p4base='//depot',
               p4branch=ConstantRenderable('render_branch'),
               p4user='user', p4client='p4_client1', p4passwd='pass'))

        client_stdin = textwrap.dedent('''\
        Client: p4_client1

        Owner: user

        Description:
        \tCreated by user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/render_branch/... //p4_client1/...\n''')

        self._full(client_stdin=client_stdin)

    def test_mode_full_renderable_p4viewspec(self):
        self.setupStep(
            P4(p4port='localhost:12000',
               mode='full',
               p4viewspec=[(ConstantRenderable('//depot/render_trunk/'), '')],
               p4user='different_user', p4client='p4_client1',
               p4passwd='pass'))

        client_stdin = textwrap.dedent('''\
        Client: p4_client1

        Owner: different_user

        Description:
        \tCreated by different_user

        Root:\t/home/user/workspace/wkdir

        Options:\tallwrite rmdir

        LineEnd:\tlocal

        View:
        \t//depot/render_trunk/... //p4_client1/...\n''')

        self._full(client_stdin=client_stdin, p4user='different_user')