# Licensed to the .NET Foundation under one or more agreements.
# The .NET Foundation licenses this file to you under the Apache 2.0 License.
# See the LICENSE file in the project root for more information.

#
# test codecs
#

'''
TODO - essentially all the tests currently here are barebones sanity checks
to ensure a minimal level of functionality exists. In other words, there are
many special cases that are not being covered *yet*.
'''

import codecs
import os
import re
import shutil
import subprocess
import sys
import unittest

from iptest import IronPythonTestCase, is_cli, is_mono, is_netcoreapp21, is_posix, run_test, skipUnlessIronPython
from iptest.misc_util import ip_supported_encodings

class CodecTest(IronPythonTestCase):
    def test_escape_decode(self):
        #sanity checks

        value, length = codecs.escape_decode("ab\a\b\t\n\r\f\vba")
        self.assertEqual(value, b'ab\x07\x08\t\n\r\x0c\x0bba')
        self.assertEqual(length, 11)

        value, length = codecs.escape_decode("\\a")
        self.assertEqual(value, b'\x07')
        self.assertEqual(length, 2)

        value, length = codecs.escape_decode("ab\a\b\t\n\r\f\vbaab\\a\\b\\t\\n\\r\\f\\vbaab\\\a\\\b\\\t\\\n\\\r\\\f\\\vba")
        self.assertEqual(value, b'ab\x07\x08\t\n\r\x0c\x0bbaab\x07\x08\t\n\r\x0c\x0bbaab\\\x07\\\x08\\\t\\\r\\\x0c\\\x0bba')
        self.assertEqual(length, 47)

        value, length = codecs.escape_decode("\\\a")
        self.assertEqual(value, b'\\\x07')
        self.assertEqual(length, 2)

        self.assertEqual(b"abc", codecs.escape_decode("abc", None)[0])
        self.assertEqual(b"?", codecs.escape_decode("\\x", 'replace')[0])
        self.assertEqual(b"?", codecs.escape_decode("\\x2", 'replace')[0])
        self.assertEqual(b"?I", codecs.escape_decode("\\xI", 'replace')[0])
        self.assertEqual(b"?II", codecs.escape_decode("\\xII", 'replace')[0])
        self.assertEqual(b"?I", codecs.escape_decode("\\x1I", 'replace')[0])
        self.assertEqual(b"?I1", codecs.escape_decode("\\xI1", 'replace')[0])

    def test_escape_encode(self):
        #sanity checks
        value, length = codecs.escape_encode(b"abba")
        self.assertEqual(value, b"abba")
        self.assertEqual(length, 4)

        value, length = codecs.escape_encode(b"ab\a\b\t\n\r\f\vba")
        self.assertEqual(value, b'ab\\x07\\x08\\t\\n\\r\\x0c\\x0bba')
        self.assertEqual(length, 11)

        value, length = codecs.escape_encode(b"\\a")
        self.assertEqual(value, b"\\\\a")
        self.assertEqual(length, 2)

        value, length = codecs.escape_encode(bytes(range(256)))
        self.assertEqual(value, b'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\x7f\\x80\\x81\\x82\\x83\\x84\\x85\\x86\\x87\\x88\\x89\\x8a\\x8b\\x8c\\x8d\\x8e\\x8f\\x90\\x91\\x92\\x93\\x94\\x95\\x96\\x97\\x98\\x99\\x9a\\x9b\\x9c\\x9d\\x9e\\x9f\\xa0\\xa1\\xa2\\xa3\\xa4\\xa5\\xa6\\xa7\\xa8\\xa9\\xaa\\xab\\xac\\xad\\xae\\xaf\\xb0\\xb1\\xb2\\xb3\\xb4\\xb5\\xb6\\xb7\\xb8\\xb9\\xba\\xbb\\xbc\\xbd\\xbe\\xbf\\xc0\\xc1\\xc2\\xc3\\xc4\\xc5\\xc6\\xc7\\xc8\\xc9\\xca\\xcb\\xcc\\xcd\\xce\\xcf\\xd0\\xd1\\xd2\\xd3\\xd4\\xd5\\xd6\\xd7\\xd8\\xd9\\xda\\xdb\\xdc\\xdd\\xde\\xdf\\xe0\\xe1\\xe2\\xe3\\xe4\\xe5\\xe6\\xe7\\xe8\\xe9\\xea\\xeb\\xec\\xed\\xee\\xef\\xf0\\xf1\\xf2\\xf3\\xf4\\xf5\\xf6\\xf7\\xf8\\xf9\\xfa\\xfb\\xfc\\xfd\\xfe\\xff')
        self.assertEqual(length, 256)

    def test_register_error(self):
            '''
            TODO: test that these are actually used.
            '''
            #Sanity
            def garbage_error0(): print("garbage_error0")
            def garbage_error1(param1): print("garbage_error1:", param1)
            def garbage_error2(param1, param2): print("garbage_error2:", param1, "; ", param2)

            codecs.register_error("garbage0", garbage_error0)
            codecs.register_error("garbage1", garbage_error1)
            codecs.register_error("garbage2", garbage_error2)
            codecs.register_error("garbage1dup", garbage_error1)

    def test_utf_16_ex_decode(self):
        #sanity
        new_str, size, zero = codecs.utf_16_ex_decode(b"abc")
        self.assertEqual(new_str, '\u6261')
        self.assertEqual(size, 2)
        self.assertEqual(zero, 0)

    def test_charmap_decode(self):
        #Sanity
        new_str, size = codecs.charmap_decode(b"abc")
        self.assertEqual(new_str, 'abc')
        self.assertEqual(size, 3)
        self.assertEqual(codecs.charmap_decode(b"a", 'strict', {ord('a') : 'a'})[0], 'a')
        self.assertEqual(codecs.charmap_decode(b"a", "replace", {})[0], '\ufffd')
        self.assertEqual(codecs.charmap_decode(b"a", "replace", {ord('a'): None})[0], '\ufffd')

        self.assertEqual(codecs.charmap_decode(b""), ('', 0))

        # using a string mapping
        self.assertEqual(codecs.charmap_decode(b'\x02\x01\x00', 'strict', "abc"), ('cba', 3))

        #Negative
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode, b"a", "strict", {})
        self.assertRaises(UnicodeDecodeError, codecs.charmap_decode, b"a", "strict", {'a': None})
        self.assertRaises(UnicodeEncodeError, codecs.charmap_encode, "a", "strict", {'a': None})
        self.assertRaises(UnicodeEncodeError, codecs.charmap_encode, "a", "replace", {'a': None})

        self.assertRaises(TypeError, codecs.charmap_decode, b"a", "strict", {ord('a'): 2.0})

    def test_decode(self):
        #sanity
        new_str = codecs.decode(b"abc")
        self.assertEqual(new_str, 'abc')

    def test_encode(self):
        #sanity
        new_str = codecs.encode("abc")
        self.assertEqual(new_str, b'abc')

    def test_raw_unicode_escape_decode(self):
        #sanity
        new_str, size = codecs.raw_unicode_escape_decode("abc")
        self.assertEqual(new_str, 'abc')
        self.assertEqual(size, 3)

    def test_raw_unicode_escape_encode(self):
        #sanity
        new_str, size = codecs.raw_unicode_escape_encode("abc")
        self.assertEqual(new_str, b'abc')
        self.assertEqual(size, 3)

    def test_utf_7_decode(self):
        #sanity
        new_str, size = codecs.utf_7_decode(b"abc")
        self.assertEqual(new_str, 'abc')
        self.assertEqual(size, 3)

    def test_utf_7_encode(self):
        #sanity
        new_str, size = codecs.utf_7_encode("abc")
        self.assertEqual(new_str, b'abc')
        self.assertEqual(size, 3)

    def test_ascii_decode(self):
        #sanity
        new_str, size = codecs.ascii_decode(b"abc")
        self.assertEqual(new_str, 'abc')
        self.assertEqual(size, 3)

    def test_ascii_encode(self):
        #sanity
        new_str, size = codecs.ascii_encode("abc")
        self.assertEqual(new_str, b'abc')
        self.assertEqual(size, 3)

    def test_latin_1_decode(self):
        #sanity
        new_str, size = codecs.latin_1_decode(b"abc")
        self.assertEqual(new_str, 'abc')
        self.assertEqual(size, 3)

    def test_latin_1_encode(self):
        #sanity
        new_str, size = codecs.latin_1_encode("abc")
        self.assertEqual(new_str, b'abc')
        self.assertEqual(size, 3)

        # so many ways to express latin 1...
        for x in ['iso-8859-1', 'iso8859-1', '8859', 'cp819', 'latin', 'latin1', 'L1']:
            self.assertEqual('abc'.encode(x), b'abc')

    #TODO: @skip("multiple_execute")
    def test_lookup_error(self):
        #sanity
        self.assertRaises(LookupError, codecs.lookup_error, "blah garbage xyz")
        def garbage_error1(someError): pass
        codecs.register_error("blah garbage xyz", garbage_error1)
        self.assertEqual(codecs.lookup_error("blah garbage xyz"), garbage_error1)
        def garbage_error2(someError): pass
        codecs.register_error("some other", garbage_error2)
        self.assertEqual(codecs.lookup_error("some other"), garbage_error2)

    #TODO: @skip("multiple_execute")
    def test_register(self):
        '''
        TODO: test that functions passed in are actually used
        '''
        #sanity check - basically just ensure that functions can be registered
        def garbage_func0(): pass
        def garbage_func1(param1): pass
        codecs.register(garbage_func0)
        codecs.register(garbage_func1)

        #negative cases
        self.assertRaises(TypeError, codecs.register)
        self.assertRaises(TypeError, codecs.register, None)
        self.assertRaises(TypeError, codecs.register, ())
        self.assertRaises(TypeError, codecs.register, [])
        self.assertRaises(TypeError, codecs.register, 1)
        self.assertRaises(TypeError, codecs.register, "abc")
        self.assertRaises(TypeError, codecs.register, 3.14)

    def test_unicode_internal_encode(self):
        # takes one or two parameters, not zero or three
        self.assertRaises(TypeError, codecs.unicode_internal_encode)
        self.assertRaises(TypeError, codecs.unicode_internal_encode, 'abc', 'def', 'qrt')
        self.assertEqual(codecs.unicode_internal_encode('abc'), (b'a\x00b\x00c\x00', 3))

    def test_unicode_internal_decode(self):
        # takes one or two parameters, not zero or three
        self.assertRaises(TypeError, codecs.unicode_internal_decode)
        self.assertRaises(TypeError, codecs.unicode_internal_decode, 'abc', 'def', 'qrt')
        self.assertEqual(codecs.unicode_internal_decode(b'ab'), ('\u6261', 2))

    def test_utf_16_be_decode(self):
        #sanity
        new_str, size = codecs.utf_16_be_decode(b"abc")
        self.assertEqual(new_str, '\u6162')
        self.assertEqual(size, 2)

    def test_utf_16_be_encode(self):
        #sanity
        new_str, size = codecs.utf_16_be_encode("abc")
        self.assertEqual(new_str, b'\x00a\x00b\x00c')
        self.assertEqual(size, 3)

    def test_utf_16_decode(self):
        #sanity
        new_str, size = codecs.utf_16_decode(b"abc")
        self.assertEqual(new_str, '\u6261')
        self.assertEqual(size, 2)

    def test_utf_16_le_decode(self):
        #sanity
        new_str, size = codecs.utf_16_le_decode(b"abc")
        self.assertEqual(new_str, '\u6261')
        self.assertEqual(size, 2)

    def test_utf_16_le_encode(self):
        #sanity
        new_str, size = codecs.utf_16_le_encode("abc")
        self.assertEqual(new_str, b'a\x00b\x00c\x00')
        self.assertEqual(size, 3)

    def test_utf_16_le_str_encode(self):
        for x in ('utf_16_le', 'UTF-16LE', 'utf-16le'):
            self.assertEqual('abc'.encode(x), b'a\x00b\x00c\x00')

    def test_utf_8_decode(self):
        #sanity
        new_str, size = codecs.utf_8_decode(b"abc")
        self.assertEqual(new_str, 'abc')
        self.assertEqual(size, 3)

    def test_cp34951(self):
        def internal_cp34951(sample1):
            self.assertEqual(codecs.utf_8_decode(sample1), ('12\u20ac\x0a', 6))
            sample1 = sample1[:-1] # 12<euro>
            self.assertEqual(codecs.utf_8_decode(sample1), ('12\u20ac', 5))
            sample1 = sample1[:-1] # 12<uncomplete euro>
            self.assertEqual(codecs.utf_8_decode(sample1), ('12', 2))

            sample1 = sample1 + b'x7f' # makes it invalid
            try:
                r = codecs.utf_8_decode(sample1)
                self.assertTrue(False, "expected UncodeDecodeError not raised")
            except Exception as e:
                self.assertEqual(type(e), UnicodeDecodeError)

        internal_cp34951(b'\x31\x32\xe2\x82\xac\x0a') # 12<euro><cr>
        if is_cli:
            internal_cp34951(b'\xef\xbb\xbf\x31\x32\xe2\x82\xac\x0a') # <BOM>12<euro><cr>

    def test_utf_8_encode(self):
        #sanity
        new_str, size = codecs.utf_8_encode("abc")
        self.assertEqual(new_str, b'abc')
        self.assertEqual(size, 3)

    def test_charmap_encode(self):
        #Sanity
        self.assertEqual(codecs.charmap_encode("abc"),
                (b'abc', 3))
        self.assertEqual(codecs.charmap_encode("abc", "strict"),
                (b'abc', 3))

        self.assertEqual(codecs.charmap_encode("", "strict", {}),
                (b'', 0))

        charmap = dict([ (ord(c), ord(c.upper())) for c in "abcdefgh"])
        self.assertEqual(codecs.charmap_encode("abc", "strict", charmap),
                (b'ABC', 3))

        #Sanity Negative
        self.assertRaises(UnicodeEncodeError, codecs.charmap_encode, "abc", "strict", {})

    @unittest.skipIf(is_posix, 'only UTF8 on posix - mbcs_decode/encode only exist on windows versions of python')
    def test_mbcs_decode(self):
        for mode in ['strict', 'replace', 'ignore', 'badmodethatdoesnotexist']:
            if is_netcoreapp21 and mode == 'badmodethatdoesnotexist': continue # FallbackBuffer created even if not used
            self.assertEqual(codecs.mbcs_decode(b'foo', mode), ('foo', 3))
            cpyres = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\u20ac\x81\u201a\u0192\u201e\u2026\u2020\u2021\u02c6\u2030\u0160\u2039\u0152\x8d\u017d\x8f\x90\u2018\u2019\u201c\u201d\u2022\u2013\u2014\u02dc\u2122\u0161\u203a\u0153\x9d\u017e\u0178\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'
            allchars = bytes(range(256))
            self.assertEqual(codecs.mbcs_decode(allchars, mode)[0], cpyres)

            # round tripping
            self.assertEqual(codecs.mbcs_encode(codecs.mbcs_decode(allchars, mode)[0])[0], allchars)

    @unittest.skipIf(is_posix, 'only UTF8 on posix - mbcs_decode/encode only exist on windows versions of python')
    def test_mbcs_encode(self):
        # these are invalid
        invalid = [0x80, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8e, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9e, 0x9f]
        uinvalid = ''.join([chr(i) for i in invalid])
        uall = ''.join([chr(i) for i in range(256) if i not in invalid])
        cpyres = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\x81\x8d\x8f\x90\x9d\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'
        for mode in ['strict', 'replace', 'ignore', 'badmodethatdoesnotexist']:
            self.assertEqual(codecs.mbcs_encode('foo', mode), (b'foo', 3))
            ipyres = codecs.mbcs_encode(uall, mode)[0]
            self.assertEqual(cpyres, ipyres)

            # all weird unicode characters that are supported
            chrs = '\u20ac\u201a\u0192\u201e\u2026\u2020\u2021\u02c6\u2030\u0160\u2039\u0152\u017d\u2018\u2019\u201c\u201d\u2022\u2013\u2014\u02dc\u2122\u0161\u203a\u0153\u017e\u0178'
            self.assertEqual(codecs.mbcs_encode(chrs, mode), (b'\x80\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8e\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9e\x9f', 27))

        self.assertEqual(codecs.mbcs_encode(uinvalid, 'replace'), (b'?'*len(uinvalid), len(uinvalid)))
        self.assertEqual(codecs.mbcs_encode(uinvalid, 'ignore'), (b'', len(uinvalid)))

    @skipUnlessIronPython()
    def test_unicode_escape_decode(self):
        self.assertRaises(NotImplementedError, codecs.unicode_escape_decode, "abc")

    @skipUnlessIronPython()
    def test_unicode_escape_encode(self):
        self.assertRaises(NotImplementedError, codecs.unicode_escape_encode, "abc")

    def test_utf_16_encode(self):
        #Sanity
        self.assertEqual(codecs.utf_16_encode("abc"), (b'\xff\xfea\x00b\x00c\x00', 3))

    def test_misc_encodings(self):
        self.assertEqual('abc'.encode('utf-16'), b'\xff\xfea\x00b\x00c\x00')
        self.assertEqual('abc'.encode('utf-16-be'), b'\x00a\x00b\x00c')
        for unicode_escape in ['unicode-escape', 'unicode escape']:
            self.assertEqual('abc'.encode('unicode-escape'), b'abc')
            self.assertEqual('abc\\u1234'.encode('unicode-escape'), b'abc\\\\u1234')

    def test_file_encodings(self):
        '''
        Tests valid PEP-236 style file encoding declarations during import
        '''

        sys.path.append(os.path.join(self.temporary_dir, "tmp_encodings"))
        try:
            os.mkdir(os.path.join(self.temporary_dir, "tmp_encodings"))
        except:
            pass

        try:
            #positive cases
            for coding in ip_supported_encodings:
                # check if the coding name matches PEP-263 requirements; this test is meaningless for names that do not match
                # https://www.python.org/dev/peps/pep-0263/#defining-the-encoding
                if not re.match('[-_.a-zA-Z0-9]+$', coding):
                    continue
                
                temp_mod_name = "test_encoding_" + coding.replace('-','_')
                with open(os.path.join(self.temporary_dir, "tmp_encodings", temp_mod_name + ".py"), "w", encoding=coding) as f:
                    # wide-char Unicode encodings need a BOM to be recognized
                    if re.match('utf[-_](16|32).', coding, re.IGNORECASE):
                        f.write("\ufeff")
                    
                    # UTF-8 with signature may only use 'utf-8' as coding (PEP-263)
                    if re.match('utf[-_]8[-_]sig$', coding, re.IGNORECASE):
                        coding = 'utf-8'
                    
                    f.write("# coding: %s" % (coding))
                
                __import__(temp_mod_name)
                os.remove(os.path.join(self.temporary_dir, "tmp_encodings", temp_mod_name + ".py"))

        finally:
            #cleanup
            sys.path.remove(os.path.join(self.temporary_dir, "tmp_encodings"))
            shutil.rmtree(os.path.join(self.temporary_dir, "tmp_encodings"), True)
        

        # handcrafted positive cases
        sys.path.append(os.path.join(self.test_dir, "encoded_files"))
        try:
            # Test that using tab of formfeed whitespace characters before "# coding ..." is OK
            # and that a tab between 'coding:' and the encoding name is OK too
            __import__('ok_encoding_whitespace')

            # Test that non-ASCII letters in the encoding name are not part of the name
            __import__('ok_encoding_nonascii')
        
        finally:
            sys.path.remove(os.path.join(self.test_dir, "encoded_files"))

    def test_file_encodings_negative(self):
        '''
        Test source file encoding errorr on import
        '''
        sys.path.append(os.path.join(self.test_dir, "encoded_files"))
        try:
            # Test that "# coding ..." declaration in the first line shadows the second line
            with self.assertRaises(SyntaxError) as cm:
                __import__("bad_encoding_name")
            # CPython's message differs when running this file, but is the same when importing it
            self.assertEqual(cm.exception.msg, "unknown encoding: bad-coding-name")

            # Test that latin-1 encoded files result in error if a coding declaration is missing
            with self.assertRaises(SyntaxError) as cm:
                __import__("bad_latin1_nodecl")
            # CPython's message differs when importing this file, but is the same when running it
            self.assertTrue(cm.exception.msg.startswith("Non-UTF-8 code starting with '\\xb5' in file"))

            # Test that latin-1 encoded files result in error if a UTF-8 BOM is present
            with self.assertRaises(SyntaxError) as cm:
                __import__("bad_latin1_bom")
            # CPython's message is the same (both on import and run)
            self.assertTrue(cm.exception.msg.startswith("(unicode error) 'utf-8' codec can't decode byte 0xb5 in position"))

            # Test that latin-1 encoded files result in error if a UTF-8 BOM is present and 'utf-8' encoding is declared
            with self.assertRaises(SyntaxError) as cm:
                __import__("bad_latin1_bom_decl")
            # CPython's message is the same (both on import and run)
            self.assertTrue(cm.exception.msg.startswith("(unicode error) 'utf-8' codec can't decode byte 0xb5 in position"))

            # Test that utf-8 encoded files result in error if a UTF-8 BOM is present and 'iso-8859-1' encoding is declared
            with self.assertRaises(SyntaxError) as cm:
                __import__("bad_utf8_bom_decl")
            # CPython's message is the same (both on import and run)
            self.assertTrue(cm.exception.msg.startswith("encoding problem: iso-8859-1 with BOM"))

            # Test that using a non-breaking whitespace inside the magic comment removes the magic
            self.assertRaises(SyntaxError, __import__, "bad_latin1_nbsp")
        
        finally:
            sys.path.remove(os.path.join(self.test_dir, "encoded_files"))

    @unittest.skipIf(is_posix, "https://github.com/IronLanguages/ironpython3/issues/541")
    @unittest.skipIf(is_mono, "https://github.com/IronLanguages/main/issues/1608")
    def test_cp11334(self):
        def run_python(filename):
            p = subprocess.Popen([sys.executable, os.path.join(self.test_dir, "encoded_files", filename)], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            t_in, t_out, t_err = (p.stdin, p.stdout, p.stderr)
            t_err_lines = t_err.readlines()
            t_out_lines = t_out.readlines()
            t_err.close()
            t_out.close()
            t_in.close()
            return t_out_lines, t_err_lines

        #--Test that not using "# coding ..." results in an error
        t_out_lines, t_err_lines = run_python("cp11334_bad.py")

        self.assertEqual(len(t_out_lines), 0)
        self.assertTrue(t_err_lines[0].startswith(b"  File"))
        self.assertTrue(t_err_lines[0].rstrip().endswith(b', line 1'))
        self.assertTrue(t_err_lines[1].startswith(b"SyntaxError: Non-UTF-8 code starting with '\\xb5' in file"))

        #--Test that using "# coding ..." is OK
        t_out_lines, t_err_lines = run_python("cp11334_ok.py")

        self.assertEqual(len(t_err_lines), 0)
        if is_cli:
            print("CodePlex 11334")
            self.assertEqual(t_out_lines[0].rstrip(), b"\xe6ble")
        else:
            self.assertEqual(t_out_lines[0].rstrip(), b"\xb5ble")
        self.assertEqual(len(t_out_lines), 1)

    def test_cp1214(self):
        """
        TODO: extend this a great deal
        """
        with self.assertRaises(LookupError):
            b'7FF80000000000007FF0000000000000'.decode('hex')

        self.assertEqual(codecs.decode(b'7FF80000000000007FF0000000000000', 'hex'),
                b'\x7f\xf8\x00\x00\x00\x00\x00\x00\x7f\xf0\x00\x00\x00\x00\x00\x00')

    def test_codecs_lookup(self):
        l = []
        def my_func(encoding, cache = l):
            l.append(encoding)

        codecs.register(my_func)
        allchars = ''.join([chr(i) for i in range(1, 256)])
        try:
            codecs.lookup(allchars)
            self.assertUnreachable()
        except LookupError:
            pass

        lowerchars = allchars.lower().replace(' ', '-')
        for i in range(1, 255):
            if l[0][i] != lowerchars[i]:
                self.assertTrue(False, 'bad chars at index %d: %r %r' % (i, l[0][i], lowerchars[i]))

        self.assertRaises(TypeError, codecs.lookup, '\0')
        self.assertRaises(TypeError, codecs.lookup, 'abc\0')
        self.assertEqual(len(l), 1)

    def test_lookup_encodings(self):
        try:
            with self.assertRaises(UnicodeError):
                b'a'.decode('undefined')
        except LookupError:
            # if we don't have encodings then this will fail so
            # make sure we're failing because we don't have encodings
            self.assertRaises(ImportError, __import__, 'encodings')

    @unittest.skipIf(is_cli, 'https://github.com/IronLanguages/main/issues/255')
    def test_cp1019(self):
        #--Test that bogus encodings fail properly
        p = subprocess.Popen([sys.executable, os.path.join(self.test_dir, "encoded_files", "cp1019.py")], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        t_in, t_out, t_err = (p.stdin, p.stdout, p.stderr)
        t_err_lines = t_err.readlines()
        t_out_lines = t_out.readlines()
        t_err.close()
        t_out.close()
        t_in.close()

        self.assertEqual(len(t_out_lines), 0)
        self.assertTrue(t_err_lines[0].startswith(b"  File"))
        if is_cli:
            self.assertTrue(t_err_lines[1].startswith(b"SyntaxError: encoding problem: with BOM"))
        else:
            self.assertTrue(t_err_lines[1].startswith(b"SyntaxError: encoding problem: garbage"))

    def test_cp20302(self):
        import _codecs
        for encoding in ip_supported_encodings:
            if encoding.lower() in ['cp1252']: #http://ironpython.codeplex.com/WorkItem/View.aspx?WorkItemId=20302
                continue
            temp = _codecs.lookup(encoding)

    def test_charmap_build(self):
        decodemap = ''.join([chr(i).upper() if chr(i).islower() else chr(i).lower() for i in range(256)])
        encodemap = codecs.charmap_build(decodemap)
        self.assertEqual(codecs.charmap_decode(b'Hello World', 'strict', decodemap), ('hELLO wORLD', 11))
        self.assertEqual(codecs.charmap_encode('Hello World', 'strict', encodemap), (b'hELLO wORLD', 11))

    def test_gh16(self):
        """https://github.com/IronLanguages/ironpython2/issues/16"""
        # test with a standard error handler
        res = "\xac\u1234\u20ac\u8000".encode("ptcp154", "backslashreplace")
        self.assertEqual(res, b"\xac\\u1234\\u20ac\\u8000")

        # test with a custom error handler
        def handler(ex):
            return ("", ex.end)
        codecs.register_error("test_unicode_error", handler)
        res = "\xac\u1234\u20ac\u8000".encode("ptcp154", "test_unicode_error")
        self.assertEqual(res, b"\xac")

run_test(__name__)
