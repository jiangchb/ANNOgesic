import sys
import os
import unittest
import shutil
from io import StringIO
sys.path.append(".")
from mock_helper import gen_file, import_data, extract_info
import annogesiclib.srna_target as st
from annogesiclib.srna_target import sRNATargetPrediction
from mock_args_container import MockClass


class Mock_func(object):

    def __init__(self):
        self.example = Example()

    def mock_run_rnaplex(self, target_seq_path, prefix, rnaplex_path):
        return 1

    def mock_run_rnaplfold(self, vienna_path, type_, win_size_s, span_s,
                           unstr_region_rnaplex_s, srna_seq_path,
                           prefix, rnaplfold_path):
        pass

    def mock_run_rnaup(self, num_up, unstr_region_rnaup,
                       out_folder, out_rnaup, out_log):
        pass

    def mock_merge_srna_target(self, rnaplex_file, rnaup_file, top, out_rnaplex,
                               out_rnaup, merge, overlap, srna, gff, fasta):
        gen_file("test_folder/out", rnaplex_file + rnaup_file)


class TestsRNATargetPrediction(unittest.TestCase):

    def setUp(self):
        self.mock_args = MockClass()
        self.example = Example()
        self.mock = Mock_func()
        self.test_folder = "test_folder"
        self.gffs = "test_folder/gffs"
        self.srnas = "test_folder/srnas"
        self.out = "test_folder/output"
        self.fastas = "test_folder/fastas"
        self.seq = "test_folder/output/sRNA_seqs"
        self.rnaup = "test_folder/output/RNAup"
        self.rnaplex = "test_folder/output/RNAplex"
        self.merge = "test_folder/output/merge"
        if (not os.path.exists(self.test_folder)):
            os.mkdir(self.test_folder)
            os.mkdir(self.gffs)
            os.mkdir(self.out)
            os.mkdir(self.srnas)
            os.mkdir(self.fastas)
            os.mkdir(self.rnaup)
            os.mkdir(self.rnaplex)
            os.mkdir(self.seq)
            os.mkdir(self.merge)
            os.mkdir(os.path.join(self.rnaup, "test"))
        args = self.mock_args.mock()
        args.out_folder = self.out
        args.srnas = self.srnas
        args.fastas = self.fastas
        args.gffs = self.gffs
        self.star = sRNATargetPrediction(args)

    def tearDown(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    def test_sort_srna_fasta(self):
        fasta = os.path.join(self.fastas, "test.fa")
        gen_file(fasta, ">aaa\nAAAAAAAA\n>bbb\nCCCC\n>ccc\nGGGGGGGGGGGG")
        self.star._sort_srna_fasta(fasta, "test", self.test_folder)
        datas = import_data(os.path.join(self.test_folder, "tmp_test_sRNA.fa"))
        self.assertListEqual(datas, ['>bbb', 'CCCC', '>aaa', 'AAAAAAAA', '>ccc', 'GGGGGGGGGGGG'])

    def test_read_fasta(self):
        fasta = os.path.join(self.fastas, "test.fa")
        gen_file(fasta, ">aaa\nAAAAAAAA")        
        seq = self.star._read_fasta(fasta)
        self.assertEqual(seq, "AAAAAAAA")

    def test_get_specific_seq(self):
        srna_file = os.path.join(self.test_folder, "aaa_sRNA.gff")
        seq_file = os.path.join(self.test_folder, "aaa.fa")
        srna_out = os.path.join(self.test_folder, "out")
        gen_file(srna_file, self.example.srna_file)
        gen_file(seq_file, self.example.seq_file)
        self.star._get_specific_seq(srna_file, seq_file, srna_out, ["aaa:5:8:+"])
        datas = import_data(srna_out)
        self.assertEqual("\n".join(datas), '>srna0|aaa|5|8|+\nTAAT')

    def test_gen_seq(self):
        srna_seq = os.path.join(self.out, "sRNA_seqs")
        tar_seq = os.path.join(self.out, "target_seqs")
        os.mkdir(os.path.join(self.srnas, "tmp"))
        os.mkdir(os.path.join(self.fastas, "tmp"))
        os.mkdir(os.path.join(self.gffs, "tmp"))
        os.mkdir(tar_seq)
        gen_file(os.path.join(self.srnas, "tmp", "aaa_sRNA.gff"), self.example.srna_file)
        gen_file(os.path.join(self.fastas, "tmp", "aaa.fa"), self.example.seq_file)
        gen_file(os.path.join(self.gffs, "tmp", "aaa.gff"), self.example.gff_file)
        args = self.mock_args.mock()
        args.query = ["aaa:5:8:+"]
        args.features = ["CDS"]
        args.tar_start = 3
        args.tar_end = 5
        self.star._gen_seq(["aaa"], args)
        datas = import_data(os.path.join(srna_seq, "aaa_sRNA.fa"))
        self.assertEqual("\n".join(datas), '>srna0|aaa|5|8|+\nTAAT')
        datas = import_data(os.path.join(tar_seq, "aaa_target_1.fa"))
        self.assertEqual("\n".join(datas), '>AAA_000001|cds0|12-16_+\nTAAATTCC')

    def test_rna_plex(self):
        self.star._run_rnaplex = self.mock.mock_run_rnaplex
        self.star._run_rnaplfold = self.mock.mock_run_rnaplfold
        os.mkdir("test_folder/test")
        gen_file("test_folder/test/test_RNAplex.txt", "test")
        gen_file(os.path.join(self.test_folder, "aaa_RNAplex.txt"), self.example.rnaplex)
        args = self.mock_args.mock()
        args.vienna_path = "test"
        args.win_size_s = 5
        args.win_size_t = 5
        args.span_s = 5
        args.span_t = 5
        args.unstr_region_rnaplex_s = 5
        args.rnaplfold_path = None
        args.unstr_region_rnaplex_t = 5
        self.star._rna_plex(["test"], args)
        datas = import_data("test_folder/test/test_RNAplex.txt")
        self.assertEqual("\n".join(datas), "test")

    def test_get_continue(self):
        out_rnaup = os.path.join(self.test_folder, "rnaup.txt")
        gen_file(out_rnaup, self.example.rnaup)
        srnas = self.star._get_continue(out_rnaup)
        self.assertListEqual(srnas, ["srna437"])

    def test_rnaup(self):
        self.star._run_rnaup = self.mock.mock_run_rnaup
        gen_file(os.path.join(self.out, "sRNA_seqs/tmp_test_sRNA.fa"), ">srna0|aaa|5|8|+\nAAATTAATTAAATTCCGGCCGGCCGG")
        gen_file(os.path.join(self.gffs, "test_target.fa"), ">AAA_000001|CDS_00000\nAAATTAATTAAATTCCGGCCGGCCGG")
        args = self.mock_args.mock()
        args.srnas = self.srnas
        args.fastas = self.fastas
        args.gffs = self.gffs
        args.vienna_path = "test"
        args.out_folder = self.out
        args.core_up = 4
        self.star._rnaup(["test"], args)
        datas = import_data(os.path.join(self.out, "tmp1.fa"))
        self.assertEqual("\n".join(datas), ">srna0|aaa|5|8|+\nAAATTAATTAAATTCCGGCCGGCCGG")

    def test_merge_rnaplex_rnaup(self):
        st.merge_srna_target = self.mock.mock_merge_srna_target
        args = self.mock_args.mock()
        args.srnas = self.srnas
        args.fastas = self.fastas
        args.gffs = self.gffs
        args.program = "both"
        args.out_folder = self.out
        args.top = "top"
        self.star._merge_rnaplex_rnaup(["test"], args)
        datas = import_data(os.path.join(self.test_folder, "out"))
        self.assertEqual("\n".join(datas), "test_folder/output/RNAplex/test/test_RNAplex.txttest_folder/output/RNAup/test/test_RNAup.txt")


class Example(object):
    srna_file = """aaa	UTR_derived	sRNA	5	8	.	+	.	ID=srna0;Name=srna_00000;UTR_type=3utr"""
    seq_file = """>aaa\nAAATTAATTAAATTCCGGCCGGCCGG"""
    gff_file = """aaa	RefSeq	CDS	12	16	.	+	.	ID=cds0;Name=CDS_00000;locus_tag=AAA_000001;Parent=gene0
aaa	RefSeq	gene	12	16	.	+	.	ID=gene0;Name=CDS_00000;locus_tag=AAA_000001"""
    rnaplex = """>SAOUHSC_00001|dnaA
>srna437
((((((((&)))))))) 163,170 :  12,19  (-2.27 = -5.08 +  1.88 +  0.93)
>SAOUHSC_00001|dnaA
>srna307
((((((((&))))))))  13,20  :  24,31  (-2.13 = -8.31 +  0.38 +  5.80)"""

    rnaup = """>srna437
>SAOUHSC_00001|dnaA
(((((((..(((((&)))))....)))))))  94,107 :  11,26  (-4.27 = -9.61 + 1.66 + 3.68)
GAUUGUUAUUAACU&AGUUAUAUAAACAAUC
>SAOUHSC_00002
.......................&................... 161,183 :   1,19  (-6.73 = -12.53 + 2.08 + 3.71)
UAUAUAAUUAUAUAUAAACGACU&AGUUGCGUAUAGUUAUAUA
>SAOUHSC_00003
((((&)))) 294,297 :   3,6   (-2.81 = -4.20 + 1.08 + 0.31)
GCAA&UUGC
>srna33
>SAOUHSC_00001|dnaA
(((((((..(((((&)))))....)))))))  94,107 :  11,26  (-4.27 = -9.61 + 1.66 + 3.68)
GAUUGUUAUUAACU&AGUUAUAUAAACAAUC
>SAOUHSC_00002
.......................&................... 161,183 :   1,19  (-6.73 = -12.53 + 2.08 + 3.71)
UAUAUAAUUAUAUAUAAACGACU&AGUUGCGUAUAGUUAUAUA
>SAOUHSC_00003
((((&)))) 294,297 :   3,6   (-2.81 = -4.20 + 1.08 + 0.31)
GCAA&UUGC"""

if __name__ == "__main__":
    unittest.main()
