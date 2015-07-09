#!/usr/bin/python

import os
import sys
import shutil
from subprocess import call
from annogesiclib.multiparser import Multiparser
from annogesiclib.helper import Helper
from annogesiclib.sRNA_intergenic import intergenic_srna
from annogesiclib.sRNA_utr_derived import utr_derived_srna
from annogesiclib.merge_sRNA import merge_srna_table, merge_srna_gff
from annogesiclib.extract_sRNA_info import extract_energy, extract_blast
from annogesiclib.plot_mountain import plot_mountain_plot
from annogesiclib.sRNA_class import classify_srna
from annogesiclib.gen_srna_output import gen_srna_table, gen_best_srna
from annogesiclib.blast_class import blast_class
from annogesiclib.compare_sRNA_sORF import srna_sorf_comparison


class sRNADetection(object):

    def __init__(self, out_folder, tsss, pros, sorf_file, fastas, trans):
        self.helper = Helper()
        self.multiparser = Multiparser()
        self.gff_output = os.path.join(out_folder, "gffs")
        self.table_output = os.path.join(out_folder, "tables")
        self.stat_path = os.path.join(out_folder, "statistics")
        self.tss_path = self._check_folder_exist(tsss)
        self.pro_path = self._check_folder_exist(pros)
        self.sorf_path = self._check_folder_exist(sorf_file)
        self.fasta_path = os.path.join(fastas, "tmp")
        self.tran_path = os.path.join(trans, "tmp")
        self.merge_wigs = os.path.join(out_folder, "merge_wigs")
        self.prefixs = {"merge": os.path.join(out_folder, "tmp_merge"),
                        "utr": os.path.join(out_folder, "tmp_utrsrna"),
                        "normal": os.path.join(out_folder, "tmp_normal"),
                        "merge_table": os.path.join(
                                       out_folder, "tmp_merge_table"),
                        "utr_table": os.path.join(
                                     out_folder, "tmp_utrsrna_table"),
                        "normal_table": os.path.join(
                                        out_folder, "tmp_normal_table"),
                        "basic": os.path.join(out_folder, "tmp_basic"),
                        "energy": os.path.join(out_folder, "tmp_energy")}
        self.tmps = {"nr": os.path.join(out_folder, "tmp_nr"),
                     "srna": os.path.join(out_folder, "tmp_sRNA")}
        self.best_table = os.path.join(self.table_output, "best")
        self.table_output = os.path.join(out_folder, "tables")
        self.stat_path = os.path.join(out_folder, "statistics")
        self.all_best = {"all_gff": os.path.join(
                                    self.gff_output, "all_candidates"),
                         "best_gff": os.path.join(self.gff_output, "best"),
                         "all_table": os.path.join(
                                      self.table_output, "all_candidates"),
                         "best_table": os.path.join(self.table_output, "best")}

    def _check_folder_exist(self, folder):
        if folder is not None:
            if "sORF" in folder:
                path = folder
            else:
                path = os.path.join(folder, "tmp")
        else:
            path = None
        return path

    def _check_gff(self, gffs):
        for gff in os.listdir(gffs):
            if gff.endswith(".gff"):
                self.helper.check_uni_attributes(os.path.join(gffs, gff))

    def _formatdb(self, database, type_, out_folder, blast_path):
        err = open(os.path.join(out_folder, "log.txt"), "w")
        if (database.endswith(".fa")) or (
            database.endswith(".fna")) or (
            database.endswith(".fasta")):
            pass
        else:
            folders = database.split("/")
            filename = folders[-1]
            folder = "/".join(folders[:-1])
            for fasta in os.listdir(folder):
                if (fasta.endswith(".fa")) or (
                    fasta.endswith(".fna")) or (
                    fasta.endswith(".fasta")):
                    if ".".join(fasta.split(".")[:-1]) == filename:
                        database = os.path.join(folder, fasta)
        db_file = ".".join(database.split(".")[:-1])
        call([os.path.join(blast_path, "makeblastdb"), "-in", database,
              "-dbtype", type_, "-out", db_file], stderr=err)

    def _run_normal(self, import_info, tss_path, pro_path, prefix, gff_path,
                    gff, tran, fuzzy_tss, max_len, min_len, wig_path, coverage,
                    merge_wigs, libs, tex_notex, replicates, table_best,
                    decrease_inter, fuzzy_inter, out_folder):
        if ("1" in import_info):
            tss = self.helper.get_correct_file(tss_path, "_TSS.gff",
                                               prefix, None)
        else:
            tss = None
        if pro_path is not None:
            pro = self.helper.get_correct_file(pro_path,
                              "_processing.gff", prefix, None)
        else:
            pro = None
        intergenic_srna(os.path.join(gff_path, gff), tran, tss, pro, fuzzy_tss,
                        max_len, min_len, os.path.join(wig_path,
                        "_".join([prefix, "forward.wig"])),
                        os.path.join(wig_path,
                        "_".join([prefix, "reverse.wig"])),
                        merge_wigs, libs, tex_notex, replicates,
                        "_".join([self.prefixs["normal"], prefix]),
                        "_".join([self.prefixs["normal_table"], prefix]),
                        table_best, decrease_inter, fuzzy_inter, coverage)

    def _run_utrsrna(self, gff_path, gff, tran, fuzzy_tss, merge_wigs, max_len,
                     min_len, wig_path, prefix, tss, pro, fasta_path, libs,
                     tex_notex, replicates, table_best, decrease_utr, fuzzy_utr,
                     utr5_coverage, utr3_coverage, intercds_coverage, out_folder):
        utr_derived_srna(os.path.join(gff_path, gff), tran, tss,
                         os.path.join(wig_path,
                         "_".join([prefix, "forward.wig"])),
                         os.path.join(wig_path,
                         "_".join([prefix, "reverse.wig"])),
                         pro, max_len, min_len, fuzzy_tss, fuzzy_utr,
                         os.path.join(fasta_path, prefix + ".fa"),
                         merge_wigs, libs, tex_notex, replicates,
                         "_".join([self.prefixs["utr"], prefix]),
                         "_".join([self.prefixs["utr_table"], prefix]),
                         table_best, decrease_utr, utr3_coverage, utr5_coverage,
                         intercds_coverage)

    def _check_necessary_file(self, gffs, trans, tex_wigs, frag_wigs, utr_srna,
                              tsss, pros, sorf_file, import_info, fastas):
        if (gffs is None) or (trans is None) or (
            (tex_wigs is None) and (frag_wigs is None)):
            print("Error: lack required files!!!!")
            sys.exit()
        if utr_srna:
            if (tsss is None):
                print("Error: lack required TSS files for UTR derived sRNA detection!!!!")
                sys.exit()
            if (pros is None):
                print("Warning: lack Processing site files for UTR derived sRNA detection!!!")
                print("it may effect the results!!!!")
        self._check_gff(gffs)
        self._check_gff(trans)
        if tsss is not None:
            self._check_gff(tsss)
            self.multiparser.parser_gff(tsss, "TSS")
            self.multiparser.combine_gff(gffs, self.tss_path, None, "TSS")
        if pros is not None:
            self._check_gff(pros)
            self.multiparser.parser_gff(pros, "processing")
            self.multiparser.combine_gff(gffs, self.pro_path,
                                          None, "processing")
        if sorf_file is not None:
            self._check_gff(sorf_file)
            self.multiparser.parser_gff(sorf_file, "TSS")
            self.multiparser.combine_gff(gffs, self.sorf_path, None, "sORF")
        if utr_srna or ("2" in import_info) or (
           "3" in import_info) or ("4" in import_info):
            if fastas is None:
                print("Error: lack required fasta files for UTR derived sRNA detection!!!!")
                sys.exit()
            self.multiparser.parser_fasta(fastas)
            self.multiparser.combine_fasta(gffs, self.fasta_path, None)
        else:
            self.fasta_path = None

    def _merge_wig(self, tex_wigs, frag_wigs, out_folder):
        if (tex_wigs is not None) and (frag_wigs is not None):
            self.helper.check_make_folder(self.merge_wigs)
            for wig in os.listdir(tex_wigs):
                if os.path.isfile(os.path.join(tex_wigs, wig)):
                    shutil.copy(os.path.join(tex_wigs, wig), self.merge_wigs)
            for wig in os.listdir(frag_wigs):
                if os.path.isfile(os.path.join(frag_wigs, wig)):
                    shutil.copy(os.path.join(frag_wigs, wig), self.merge_wigs)
        elif (tex_wigs is not None):
            self.merge_wigs = tex_wigs
        elif (frag_wigs is not None):
            self.merge_wigs = frag_wigs
        return self.merge_wigs

    def _merge_libs(self, tlibs, flibs):
        if (tlibs is None) and (flibs is None):
            print("Error: please input proper libraries!!")
        if (tlibs is not None) and (flibs is not None):
            libs = tlibs + flibs
        elif (tlibs is not None):
            libs = tlibs
        elif (flibs is not None):
            libs = flibs
        return libs

    def _run_program(self, gff_path, import_info, tran_path, tss_path, pro_path,
                     wig_path, max_len, min_len, coverage, merge_wigs, libs,
                     tex_notex, replicates, table_best, decrease_inter,
                     decrease_utr, fuzzy_inter, fuzzy_utr, fuzzy_tsss,
                     utr5_coverage, utr3_coverage, intercds_coverage,
                     out_folder, utr_srna, fasta_path):
        prefixs = []
        for gff in os.listdir(gff_path):
            if gff.endswith(".gff"):
                prefix = gff.replace(".gff", "")
                prefixs.append(prefix)
                print("Running sRNA detection of {0}....".format(prefix))
                tran = self.helper.get_correct_file(tran_path,
                            "_transcript.gff", prefix, None)
                merge_gff = "_".join([self.prefixs["merge"], prefix])
                utr_gff = "_".join([self.prefixs["utr"], prefix])
                normal_gff = "_".join([self.prefixs["normal"], prefix])
                merge_table = "_".join([self.prefixs["merge_table"], prefix])
                utr_table = "_".join([self.prefixs["utr_table"], prefix])
                normal_table = "_".join([self.prefixs["normal_table"], prefix])
                self._run_normal(import_info, tss_path, pro_path, prefix,
                                 gff_path, gff, tran, fuzzy_tsss["inter"],
                                 max_len, min_len, wig_path, coverage,
                                 merge_wigs, libs, tex_notex, replicates,
                                 table_best, decrease_inter, fuzzy_inter, out_folder)
                if utr_srna:
                    print("Running UTR derived sRNA detection of {0}...".format(
                          prefix))
                    tss = self.helper.get_correct_file(tss_path, "_TSS.gff",
                                                       prefix, None)
                    if pro_path is not None:
                        pro = self.helper.get_correct_file(pro_path,
                                          "_processing.gff", prefix, None)
                    else:
                        pro = None
                    if tss is not None:
                        self._run_utrsrna(gff_path, gff, tran, fuzzy_tsss,
                                 merge_wigs, max_len, min_len, wig_path, prefix,
                                 tss, pro, fasta_path, libs, tex_notex,
                                 replicates, table_best, decrease_utr,
                                 fuzzy_utr, utr5_coverage, utr3_coverage,
                                 intercds_coverage, out_folder)
                        # merge intergenic and UTR derived sRNA   #
                print("merging data of intergenic and UTR_derived sRNA...")
                merge_srna_gff(utr_gff, normal_gff, merge_gff)
                merge_srna_table(merge_gff, normal_table, utr_table,
                                 os.path.join(wig_path,
                                 "_".join([prefix, "forward.wig"])),
                                 os.path.join(wig_path,
                                 "_".join([prefix, "reverse.wig"])),
                                 merge_wigs, libs, tex_notex, replicates,
                                 table_best, merge_table)
                self.helper.sort_gff(merge_gff,
                            "_".join([self.prefixs["basic"], prefix]))
        return prefixs

    def _get_seq_sec(self, fasta_path, out_folder, prefix, sec_path,
                     dot_path, vienna_path):
        detect = False
        for fasta in os.listdir(fasta_path):
            if fasta.endswith(".fa") and (
               fasta.replace(".fa", "") == prefix):
                detect = True
                break
        if detect:
            detect = False
            seq_file = os.path.join(out_folder, "_".join(["sRNA_seq", prefix]))
            sec_file = os.path.join(out_folder, "_".join(["sRNA_2d", prefix]))
            self.helper.get_seq("_".join([self.prefixs["basic"], prefix]),
                                os.path.join(fasta_path, fasta), seq_file)
        else:
            print("Error:There is not fasta file of {0}".format(prefix))
        tmp_path = os.path.join(out_folder, "tmp_srna")
        self.helper.check_make_folder(tmp_path)
        main_path = os.getcwd()
        os.chdir(tmp_path)
        sec_file = os.path.join(main_path, sec_file)
        seq_file = os.path.join(main_path, seq_file)
        ## the same as sec_path, just modify for fit os.chdir
        tmp_sec_path = os.path.join(main_path, sec_path)
        tmp_dot_path = os.path.join(main_path, dot_path)
        os.system(" ".join(["cat", seq_file, "|",
                  os.path.join(vienna_path, "Progs", "RNAfold"),
                  "-p", ">", sec_file]))
        extract_energy(os.path.join(main_path,
                       "_".join([self.prefixs["basic"], prefix])),
                       sec_file, os.path.join(main_path,
                       "_".join([self.prefixs["energy"], prefix])))
        for ps in os.listdir(os.getcwd()):
            new_ps = ps.replace("|", "_")
            os.rename(ps, new_ps)
        return {"sec": tmp_sec_path, "dot": tmp_dot_path, "main": main_path,
                "tmp": os.path.join(main_path, tmp_path)}

    def _replot_sec_to_pdf(self, vienna_path, tmp_paths, ps2pdf14_path, prefix):
        ### now we are in out_folder/tmp_srna
        for file_ in os.listdir(os.getcwd()):
            if file_.endswith("ss.ps"):
                dot_file = file_.replace("ss.ps", "dp.ps")
                rel_file = file_.replace("ss.ps", "rss.ps")
                print("replot {0}".format(file_))
                os.system(" ".join(["perl",
                          os.path.join(vienna_path, "Utils", "relplot.pl"),
                          os.path.join(tmp_paths["tmp"], file_),
                          os.path.join(tmp_paths["tmp"], dot_file),
                          ">", os.path.join(tmp_paths["tmp"], rel_file)]))
        for file_ in os.listdir(tmp_paths["tmp"]):
            if (file_.endswith("rss.ps")) or (file_.endswith("dp.ps")):
                pdf_file = file_.replace(".ps", ".pdf")
                print("convert {0} to pdf".format(file_))
                call([ps2pdf14_path,
                      os.path.join(tmp_paths["tmp"], file_), pdf_file])
        os.mkdir(os.path.join(tmp_paths["sec"], prefix))
        os.mkdir(os.path.join(tmp_paths["dot"], prefix))
        self.helper.move_all_content(tmp_paths["tmp"],
                 os.path.join(tmp_paths["sec"], prefix), ["rss.pdf"])
        self.helper.move_all_content(tmp_paths["tmp"],
                 os.path.join(tmp_paths["dot"], prefix), ["dp.pdf"])

    def _plot_mountain(self, mountain, moun_path,
                       tmp_paths, prefix, vienna_path):
        if mountain:
            tmp_moun_path = os.path.join(tmp_paths["main"], moun_path)
            os.mkdir(os.path.join(tmp_moun_path, prefix))
            txt_path = os.path.join(tmp_paths["tmp"], "tmp_txt")
            self.helper.check_make_folder(txt_path)
            print("Generating mountain plot of {0}....".format(prefix))
            for dot_file in os.listdir(tmp_paths["tmp"]):
                if dot_file.endswith("dp.ps"):
                    moun_txt = os.path.join(tmp_paths["tmp"], "mountain.txt")
                    out = open(moun_txt, "w")
                    moun_file = dot_file.replace("dp.ps", "mountain.pdf")
                    print("Generating {0}".format(moun_file))
                    call(["perl",
                          os.path.join(vienna_path, "Utils", "mountain.pl"),
                          os.path.join(tmp_paths["tmp"], dot_file)], stdout=out)
                    plot_mountain_plot(moun_txt, moun_file)
                    os.rename(moun_file,
                              os.path.join(tmp_moun_path, prefix, moun_file))
                    out.close()
                    os.remove(moun_txt)

    def _compute_2d_and_energy(self, out_folder, prefixs, fasta_path,
                               vienna_path, mountain, ps2pdf14_path):
        print("Running energy calculation....")
        moun_path = os.path.join(out_folder, "mountain_plot")
        sec_path = os.path.join(out_folder, "sec_structure", "sec_plot")
        dot_path = os.path.join(out_folder, "sec_structure", "dot_plot")
        self.helper.remove_all_content(sec_path, None, "dir")
        self.helper.remove_all_content(dot_path, None, "dir")
        self.helper.remove_all_content(moun_path, None, "dir")
        for prefix in prefixs:
            tmp_paths = self._get_seq_sec(fasta_path, out_folder, prefix,
                                          sec_path, dot_path, vienna_path)
            self._replot_sec_to_pdf(vienna_path, tmp_paths,
                                    ps2pdf14_path, prefix)
            self._plot_mountain(mountain, moun_path, tmp_paths,
                                prefix, vienna_path)
            self.helper.remove_all_content(os.getcwd(), ".ps", "file")
            os.chdir(tmp_paths["main"])
            os.rename("_".join([self.prefixs["energy"], prefix]),
                      "_".join([self.prefixs["basic"], prefix]))
            shutil.rmtree(os.path.join(out_folder, "tmp_srna"))

    def _blast(self, database, database_format, data_type, out_folder,
               blast_path, prefixs, fasta_path, program, database_type, e):
        if (database is None):
            print("Error: No database assigned!")
        else:
            if database_format:
                self._formatdb(database, data_type, out_folder, blast_path)
            for prefix in prefixs:
                blast_file = os.path.join(out_folder, "blast_result_and_misc",
                             "_".join([database_type, "blast",
                                       prefix + ".txt"]))
                srna_file = "_".join([self.prefixs["basic"], prefix])
                out_file = os.path.join(out_folder,
                           "_".join(["tmp", database_type, prefix]))
                print("Running Blast of {0}".format(prefix))
                seq_file = os.path.join(out_folder,
                           "_".join(["sRNA_seq", prefix]))
                if seq_file not in os.listdir(out_folder):
                    self.helper.get_seq(srna_file,
                         os.path.join(fasta_path, prefix + ".fa"), seq_file)
                call([os.path.join(blast_path, program), "-db", database,
                      "-evalue", str(e), "-query", seq_file,
                      "-out", blast_file])
                extract_blast(blast_file, srna_file, out_file,
                              out_file + ".csv", database_type)
                os.rename(out_file, srna_file)

    def _class_srna(self, import_info, prefixs, gff_output, table_output, stat_path,
                    energy, nr_hit_num, max_len, min_len):
        if (len(import_info) != 1) or ('6' not in import_info):
            for prefix in prefixs:
                print("classifying sRNA of {0}".format(prefix))
                class_gff = os.path.join(gff_output, "for_class")
                class_table = os.path.join(table_output, "for_class")
                self.helper.check_make_folder(os.path.join(class_table, prefix))
                self.helper.check_make_folder(os.path.join(class_gff, prefix))
                class_gff = os.path.join(class_gff, prefix)
                class_table = os.path.join(class_table, prefix)
                self.helper.check_make_folder(class_table)
                self.helper.check_make_folder(class_gff)
                out_stat = os.path.join(stat_path,
                           "_".join(["stat_sRNA_class", prefix + ".csv"]))
                classify_srna(os.path.join(self.all_best["all_gff"],
                              "_".join([prefix, "sRNA.gff"])),
                              class_gff, energy, nr_hit_num, out_stat)
                for srna in os.listdir(class_gff):
                    out_table = os.path.join(class_table,
                                srna.replace(".gff", ".csv"))
                    print(os.path.join(class_gff, srna))
                    gen_srna_table(os.path.join(class_gff, srna),
                        "_".join([self.prefixs["merge_table"], prefix]),
                        "_".join([self.tmps["nr"], prefix + ".csv"]),
                        "_".join([self.tmps["srna"], prefix + ".csv"]),
                        max_len, min_len, out_table)

    def _get_best_result(self, prefixs, energy,
                         nr_hit_num, all_hit, best_sorf, max_len, min_len):
        for prefix in prefixs:
            best_gff = os.path.join(self.all_best["best_gff"],
                                    "_".join([prefix, "sRNA.gff"]))
            best_table = os.path.join(self.all_best["best_table"],
                                      "_".join([prefix, "sRNA.csv"]))
            gen_best_srna(os.path.join(self.all_best["all_gff"],
                                       "_".join([prefix, "sRNA.gff"])),
                          all_hit, energy, nr_hit_num, best_sorf, best_gff)
            gen_srna_table(os.path.join(self.all_best["best_gff"],
                           "_".join([prefix, "sRNA.gff"])),
                           "_".join([self.prefixs["merge_table"], prefix]),
                           "_".join([self.tmps["nr"], prefix + ".csv"]),
                           "_".join([self.tmps["srna"], prefix + ".csv"]),
                           max_len, min_len, best_table)

    def _remove_file(self, out_folder, fastas, gffs, frag_wigs, tex_wigs,
                     tsss, trans, pros, sorf_file, merge_wigs):
        self.helper.remove_all_content(out_folder, "tmp_", "dir")
        self.helper.remove_all_content(out_folder, "tmp_", "file")
        self.helper.remove_tmp(fastas)
        self.helper.remove_tmp(gffs)
        if frag_wigs is not None:
            self.helper.remove_tmp(frag_wigs)
        if tex_wigs is not None:
            self.helper.remove_tmp(tex_wigs)
        if (frag_wigs is not None) and (
            tex_wigs is not None):
            shutil.rmtree(merge_wigs)
        self.helper.remove_tmp(trans)
        if tsss is not None:
            self.helper.remove_tmp(tsss)
        if pros is not None:
            self.helper.remove_tmp(pros)
        if sorf_file is not None:
            self.helper.remove_tmp(sorf_file)

    def _filter_srna(self, import_info, out_folder, prefixs, fasta_path,
                     vienna_path, mountain, ps2pdf14_path, nr_database,
                     database_format, blast_path, srna_database,
                     stat_path, sorf_path, e_nr, e_srna):
        if "2" in import_info:
            self._compute_2d_and_energy(out_folder, prefixs, fasta_path,
                                        vienna_path, mountain, ps2pdf14_path)
        if "3" in import_info:
            self._blast(nr_database, database_format, "prot", out_folder,
                        blast_path, prefixs, fasta_path, "blastx", "nr", e_nr)
        if "4" in import_info:
            self._blast(srna_database, database_format, "nucl", out_folder,
                        blast_path, prefixs, fasta_path,
                        "blastn", "sRNA", e_srna)
            for prefix in prefixs:
                out_srna_blast = os.path.join(stat_path,
                                 "_".join(["stat_sRNA_blast_class",
                                 prefix + ".csv"]))
                blast_class("_".join([self.tmps["srna"], prefix + ".csv"]),
                            out_srna_blast)
        if "5" in import_info:
            if "_".join([prefix, "sORF.gff"]) in os.listdir(sorf_path):
                tmp_srna = os.path.join(out_folder,
                           "".join(["tmp_srna_sorf", prefix]))
                tmp_sorf = os.path.join(out_folder,
                           "".join(["tmp_sorf_srna", prefix]))
                srna_sorf_comparison("_".join([self.prefixs["basic"], prefix]),
                                     os.path.join(sorf_path,
                                     "_".join([prefix, "sORF.gff"])),
                                     tmp_srna, tmp_sorf)
                os.remove(tmp_sorf)
                os.rename(tmp_srna, "_".join([self.prefixs["basic"], prefix]))

    def _get_replicates(self, replicates_tex, replicates_frag):
        if (replicates_tex is not None) and (
            replicates_frag is not None):
            replicates = {"tex": int(replicates_tex),
                          "frag": int(replicates_frag)}
        elif replicates_tex is not None:
            replicates = {"tex": int(replicates_tex), "frag": -1}
        elif replicates_frag is not None:
            replicates = {"tex": -1, "frag": int(replicates_frag)}
        else:
            print("Error:No replicates number assign!!!")
            sys.exit()
        return replicates

    def run_srna_detection(self, vienna_path, blast_path, ps2pdf14_path,
            out_folder, utr_srna, gffs, tsss, trans, fuzzy_inter_tss,
            fuzzy_5utr_tss, fuzzy_3utr_tss, fuzzy_intercds_tss, import_info,
            tex_wigs, frag_wigs, pros, fastas, mountain, database_format,
            srna_database, nr_database, energy, coverage, utr5_coverage,
            utr3_coverage, intercds_coverage, max_len, min_len, tlibs, flibs,
            replicates_tex, replicates_frag, tex_notex, e_nr, e_srna,
            table_best, decrease_inter, decrease_utr, fuzzy_inter, fuzzy_utr,
            nr_hits_num, sorf_file, all_hit, best_sorf):
        replicates = self._get_replicates(replicates_tex, replicates_frag)
        fuzzy_tsss = {"5utr": fuzzy_5utr_tss, "3utr": fuzzy_3utr_tss,
                      "interCDS": fuzzy_intercds_tss, "inter": fuzzy_inter_tss}
        self.multiparser.parser_gff(gffs, None)
        self._check_necessary_file(gffs, trans, tex_wigs, frag_wigs,
             utr_srna, tsss, pros, sorf_file, import_info, fastas)
        merge_wigs = self._merge_wig(tex_wigs, frag_wigs, out_folder)
        wig_path = os.path.join(merge_wigs, "tmp")
        self.multiparser.parser_wig(merge_wigs)
        self.multiparser.combine_wig(gffs, wig_path, None)
        self.multiparser.parser_gff(trans, "transcript")
        self.multiparser.combine_gff(gffs, self.tran_path, None, "transcript")
        libs = self._merge_libs(tlibs, flibs)
        prefixs = self._run_program(gffs, import_info, self.tran_path,
                      self.tss_path, self.pro_path, wig_path, max_len, min_len,
                      coverage, merge_wigs, libs, tex_notex, replicates,
                      table_best, decrease_inter, decrease_utr, fuzzy_inter,
                      fuzzy_utr, fuzzy_tsss, utr5_coverage, utr3_coverage,
                      intercds_coverage, out_folder, utr_srna, self.fasta_path)
        self._filter_srna(import_info, out_folder, prefixs, self.fasta_path,
            vienna_path, mountain, ps2pdf14_path, nr_database, database_format,
            blast_path, srna_database, self.stat_path, self.sorf_path, e_nr,
            e_srna)
        for prefix in prefixs:
            shutil.copyfile("_".join([self.prefixs["basic"], prefix]),
                            os.path.join(self.all_best["all_gff"],
                            "_".join([prefix, "sRNA.gff"])))
        for prefix in prefixs:
            out_table = os.path.join(self.all_best["all_table"],
                                     "_".join([prefix, "sRNA.csv"]))
            gen_srna_table(os.path.join(self.all_best["all_gff"],
                           "_".join([prefix, "sRNA.gff"])),
                           "_".join([self.prefixs["merge_table"], prefix]),
                           "_".join([self.tmps["nr"], prefix + ".csv"]),
                           "_".join([self.tmps["srna"], prefix + ".csv"]),
                           max_len, min_len, out_table)
        self._class_srna(import_info, prefixs, self.gff_output, self.table_output,
             self.stat_path, energy, nr_hits_num, max_len, min_len)
        self._get_best_result(prefixs, energy, nr_hits_num,
                              all_hit, best_sorf, max_len, min_len)
        self._remove_file(out_folder, fastas, gffs, frag_wigs, tex_wigs,
             tsss, trans, pros, sorf_file, merge_wigs)