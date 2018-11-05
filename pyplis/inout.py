# -*- coding: utf-8 -*-
#
# Pyplis is a Python library for the analysis of UV SO2 camera data
# Copyright (C) 2017 Jonas Gliss (jonasgliss@gmail.com)
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License a
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""Module containing all sorts of I/O-routines (e.g. test data access)."""
from os.path import join, basename, exists, isfile, abspath, expanduser
from os import listdir, mkdir, remove, walk
from re import split

from collections import OrderedDict as od
try:
    from progressbar import ProgressBar, Percentage, Bar, RotatingMarker,\
        ETA, FileTransferSpeed
    PGBAR_AVAILABLE = True
except BaseException:
    PGBAR_AVAILABLE = False
from zipfile import ZipFile, ZIP_DEFLATED
from urllib import urlretrieve
from urllib2 import urlopen
from tempfile import mktemp, gettempdir
from shutil import copy2


def data_search_dirs():
    """Get basic search directories for package data files."""
    from pyplis import __dir__
    usr_dir = expanduser(join('~', 'my_pyplis'))
    if not exists(usr_dir):
        mkdir(usr_dir)
    return (usr_dir, join(__dir__, "data"))


def zip_example_scripts(repo_base):
    from pyplis import __version__ as v
    vstr = ".".join(v.split(".")[:3])
    print("Adding zipped version of pyplis example scripts for version %s" %
          vstr)
    scripts_dir = join(repo_base, "scripts")
    if not exists(scripts_dir):
        raise IOError("Cannot created zipped version of scripts, folder %s "
                      "does not exist" % scripts_dir)
    save_dir = join(scripts_dir, "old_versions")
    if not exists(save_dir):
        raise IOError("Cannot create zipped version of scripts, folder %s "
                      "does not exist" % save_dir)
    name = "scripts-%s.zip" % vstr
    zipf = ZipFile(join(save_dir, name), 'w', ZIP_DEFLATED)
    for fname in listdir(scripts_dir):
        if fname.endswith("py"):
            zipf.write(join(scripts_dir, fname))
    zipf.close()


def get_all_files_in_dir(directory, file_type=None, include_sub_dirs=False):
    """Find all files in a certain directory.

    Parameters
    ----------
    directory : str
        path to directory
    file_type : :obj:`str`, optional
        specify file type (e.g. "png", "fts"). If unspecified, then all files
        are considered
    include_sub_dirs : bool
        if True, also all files from all sub-directories are extracted

    Returns
    -------
    list
        sorted list containing paths of all files detected

    """
    p = directory
    if p is None or not exists(p):
        message = ('Error: path %s does not exist' % p)
        print(message)
        return []
    use_all_types = False
    if not isinstance(file_type, str):
        use_all_types = True

    if include_sub_dirs:
        print("Include files from subdirectories")
        all_paths = []
        if use_all_types:
            print("Using all file types")
            for path, subdirs, files in walk(p):
                for filename in files:
                    all_paths.append(join(path, filename))
        else:
            print("Using only %s files" % file_type)
            for path, subdirs, files in walk(p):
                for filename in files:
                    if filename.endswith(file_type):
                        all_paths.append(join(path, filename))

    else:
        print("Exclude files from subdirectories")
        if use_all_types:
            print("Using all file types")
            all_paths = [join(p, f) for f in listdir(p) if isfile(join(p, f))]
        else:
            print("Using only %s files" % file_type)
            all_paths = [join(p, f) for f in listdir(p) if
                         isfile(join(p, f)) and f.endswith(file_type)]
    all_paths.sort()
    return all_paths


def create_temporary_copy(path):
    temp_dir = gettempdir()
    temp_path = join(temp_dir, basename(path))
    copy2(path, temp_path)
    return temp_path


def download_test_data(save_path=None):
    """Download pyplis test data.

    :param save_path: location where path is supposed to be stored

    Code for progress bar was "stolen" `here <http://stackoverflow.com/
    questions/11143767/how-to-make-a-download-with>`_
    (last access date: 11/01/2017)
    -progress-bar-in-python

    """
    from pyplis import URL_TESTDATA
    url = URL_TESTDATA

    dirs = data_search_dirs()
    where = dirs[0]
    fp = join(where, "_paths.txt")
    if not exists(fp):
        where = dirs[1]
        fp = join(where, "_paths.txt")
    if save_path is None or not exists(save_path):
        save_path = where
        print("Save path unspecified")
    else:
        with open(fp, "a") as f:
            f.write("\n" + save_path + "\n")
            print("Adding new path for test data location in "
                  "file _paths.txt: %s" % save_path)
            f.close()

    print("installing test data at %s" % save_path)

    filename = mktemp('.zip')

    if PGBAR_AVAILABLE:
        widgets = ['Downloading pyplis test data: ', Percentage(), ' ',
                   Bar(marker=RotatingMarker()), ' ',
                   ETA(), ' ', FileTransferSpeed()]

        pbar = ProgressBar(widgets=widgets)

        def dl_progress(count, block_size, total_size):
            if pbar.maxval is None:
                pbar.maxval = total_size
                pbar.start()
            pbar.update(min(count * block_size, total_size))

        urlretrieve(url, filename, reporthook=dl_progress)
        pbar.finish()
    else:
        print("Downloading Pyplis testdata (this can take a while, install"
              "Progressbar package if you want to receive download info")
        urlretrieve(url, filename)
    thefile = ZipFile(filename)
    print("Extracting data at: %s (this may take a while)" % save_path)
    thefile.extractall(save_path)
    thefile.close()
    remove(filename)
    print("Download successfully finished, deleted temporary data file"
          "at: %s" % filename)


def find_test_data():
    """Search location of test data folder."""
    dirs = data_search_dirs()
    folder_name = "pyplis_etna_testdata"
    for data_path in dirs:
        if folder_name in listdir(data_path):
            print("Found test data at location: %s" % data_path)
            return join(data_path, folder_name)
        try:
            with open(join(data_path, "_paths.txt"), "r") as f:
                lines = f.readlines()
                for line in lines:
                    p = line.split("\n")[0]
                    if exists(p) and folder_name in listdir(p):
                        print("Found test data at default location: %s" % p)
                        f.close()
                        return join(p, folder_name)
        except:
            pass
    raise IOError("pyplis test data could not be found, please download"
                  "testdata first, using method "
                  "pyplis.inout.download_test_data or"
                  "specify the local path where the test data is stored using"
                  "pyplis.inout.set_test_data_path")


def all_test_data_paths():
    """Return list of all search paths for test data."""
    dirs = data_search_dirs()
    paths = []
    [paths.append(x) for x in dirs]
    for data_path in dirs:
        fp = join(data_path, "_paths.txt")
        if exists(fp):
            with open(join(data_path, "_paths.txt"), "r") as f:
                lines = f.readlines()
                for line in lines:
                    p = line.split("\n")[0].lower()
                    if exists(p):
                        paths.append(p)
    return paths


def set_test_data_path(save_path):
    """Set local path where test data is stored."""
    if save_path.lower() in all_test_data_paths():
        print("Path is already in search tree")
        return
    dirs = data_search_dirs()
    fp = join(dirs[0], "_paths.txt")
    if not exists(fp):
        fp = join(dirs[1], "_paths.txt")
    save_path = abspath(save_path)
    try:
        if not exists(save_path):
            raise IOError("Could not set test data path: specified location "
                          "does not exist: %s" % save_path)
        with open(fp, "a") as f:
            f.write("\n" + save_path + "\n")
            print("Adding new path for test data location in "
                  "file _paths.txt: %s" % save_path)
            f.close()
        if "pyplis_etna_testdata" not in listdir(save_path):
            print("WARNING: test data folder (name: pyplis_etna_testdata) "
                  "could not be  found at specified location, please download "
                  "test data, unzip and save at: %s" % save_path)
    except:
        raise


def _load_cam_info(cam_id, filepath):
    """Load camera info from a specific cam_info file."""
    dat = od()
    if cam_id is None:
        return dat
    with open(filepath) as f:
        filters = []
        darkinfo = []
        io_opts = {}
        found = 0
        for ll in f:
            line = ll.rstrip()
            if line:
                if "END" in line and found:
                    dat["default_filters"] = filters
                    dat["dark_info"] = darkinfo
                    dat["io_opts"] = io_opts
                    return dat
                spl = line.split(":")
                if found:
                    if line[0] != "#":
                        spl = line.split(":")
                        k = spl[0].strip()
                        if k == "dark_info":
                            l = [x.strip()
                                 for x in spl[1].split("#")[0].split(',')]
                            darkinfo.append(l)
                        elif k == "filter":
                            l = [x.strip()
                                 for x in spl[1].split("#")[0].split(',')]
                            filters.append(l)
                        elif k == "io_opts":
                            l = [x.strip()
                                 for x in split("=|,", spl[1].split("#")[0])]
                            keys, vals = l[::2], l[1::2]
                            if len(keys) == len(vals):
                                for i in range(len(keys)):
                                    io_opts[keys[i]] = bool(int(vals[i]))
                        elif k == "reg_shift_off":
                            try:
                                l = [float(x.strip()) for x in
                                     spl[1].split("#")[0].split(',')]
                                dat["reg_shift_off"] = l
                            except:
                                pass
                        else:
                            data_str = spl[1].split("#")[0].strip()
                            if any([data_str == x for x in ["''", '""']]):
                                data_str = ""
                            dat[k] = data_str
                if spl[0] == "cam_ids":
                    l = [x.strip() for x in spl[1].split("#")[0].split(',')]
                    if cam_id in l:
                        found = 1
                        dat["cam_ids"] = l
    raise IOError("Camera info for cam_id %s could not be found" % cam_id)


def get_camera_info(cam_id):
    """Try access camera information from file "cam_info.txt" (package data).

    :param str cam_id: string ID of camera (e.g. "ecII")

    """
    dirs = data_search_dirs()
    try:
        return _load_cam_info(cam_id, join(dirs[0], "cam_info.txt"))
    except:
        return _load_cam_info(cam_id, join(dirs[1], "cam_info.txt"))


def save_new_default_camera(info_dict):
    """Save new default camera to data file *cam_info.txt*.

    :param dict info_dict: dictionary containing camera default information

    Only valid keys will be added to the
    """
    dirs = data_search_dirs()
    cam_file = join(dirs[0], "cam_info.txt")
    if not exists(cam_file):
        cam_file = join(dirs[1], "cam_info.txt")
    keys = get_camera_info("ecII").keys()
    for key in keys:
        print("%s (in input: %s)" % (key, key in info_dict))
    if "cam_id" not in info_dict:
        raise KeyError("Missing specification of cam_id")
    try:
        cam_ids = info_dict["cam_ids"]
    except:
        info_dict["cam_ids"] = [info_dict["cam_id"]]
        cam_ids = [info_dict["cam_id"]]
    if not all([x in info_dict.keys() for x in keys]):
        raise KeyError("Input dictionary does not include all required keys "
                       "for creating a new default camera type, required "
                       "keys are %s" % keys)
    ids = get_all_valid_cam_ids()
    if any([x in ids for x in info_dict["cam_ids"]]):
        raise KeyError("Cam ID conflict: one of the provided IDs already "
                       "exists in database...")

    cam_file_temp = create_temporary_copy(cam_file)
    with open(cam_file_temp, "a") as info_file:
        info_file.write("\n\nNEWCAM\ncam_ids:")
        cam_ids = [str(x) for x in cam_ids]
        info_file.write(",".join(cam_ids))
        info_file.write("\n")
        for k, v in info_dict.iteritems():
            if k in keys:
                if k == "default_filters":
                    for finfo in v:
                        info_file.write("filter:")
                        finfo = [str(x) for x in finfo]
                        info_file.write(",".join(finfo))
                        info_file.write("\n")
                elif k == "dark_info":
                    for finfo in v:
                        info_file.write("dark_info:")
                        finfo = [str(x) for x in finfo]
                        info_file.write(",".join(finfo))
                        info_file.write("\n")
                elif k == "io_opts":
                    s = "io_opts:"
                    for opt, val in v.iteritems():
                        s += "%s=%d," % (opt, val)
                    s = s[:-1] + "\n"
                    info_file.write(s)
                elif k == "reg_shift_off":
                    info_file.write("%s:%.2f,%.2f\n" % (k, v[0], v[1]))
                elif k == "cam_ids":
                    pass
                else:
                    info_file.write("%s:%s\n" % (k, v))
        info_file.write("ENDCAM")
    info_file.close()
    # Writing ended without errors: replace data base file "cam_info.txt" with
    # the temporary file and delete the temporary file
    copy2(cam_file_temp, cam_file)
    remove(cam_file_temp)

    print("Successfully added new default camera %s to database at %s"
          % (info_dict["cam_id"], cam_file))


def save_default_source(info_dict):
    """Add a new default source to file source_info.txt."""
    if not all(k in info_dict for k in ("name", "lon", "lat", "altitude")):
        raise ValueError("Cannot save source information, require at least "
                         "name, lon, lat and altitude")

    dirs = data_search_dirs()
    path = join(dirs[0], "my_sources.txt")
    if not exists(path):
        path = join(dirs[1], "my_sources.txt")
    if info_dict["name"] in get_source_ids():
        raise NameError("A source with name %s already exists in database"
                        % info_dict["name"])

    source_file_temp = create_temporary_copy(path)
    with open(source_file_temp, "a") as info_file:
        info_file.write("\n\nsource_ids:%s\n" % info_dict["name"])
        for k, v in info_dict.iteritems():
            info_file.write("%s:%s\n" % (k, v))
        info_file.write("END")
    info_file.close()
    # Writing ended without errors: replace data base file "cam_info.txt" with
    # the temporary file and delete the temporary file
    copy2(source_file_temp, path)
    remove(source_file_temp)

    print("Successfully added new default source %s to database file at %s"
          % (info_dict["name"], path))


def get_all_valid_cam_ids():
    """Load all valid camera string ids.

    Reads info from file cam_info.txt which is part of package data
    """
    from pyplis import _LIBDIR
    ids = []
    with open(join(_LIBDIR, "data", "cam_info.txt")) as f:
        for line in f:
            spl = line.split(":")
            if spl[0].strip().lower() == "cam_ids":
                ids.extend([x.strip()
                            for x in spl[1].split("#")[0].split(',')])
    return ids


def get_cam_ids():
    """Load all default camera string ids.

    Reads info from file cam_info.txt which is part of package data
    """
    dirs = data_search_dirs()
    ids = []
    for path in dirs:
        try:
            with open(join(path, "cam_info.txt")) as f:
                for line in f:
                    spl = line.split(":")
                    if spl[0].strip().lower() == "cam_id":
                        sid = spl[1].split("#")[0].strip()
                        if sid not in ids:
                            ids.append(sid)
        except IOError:
            pass

    return ids


def get_source_ids():
    """Get all existing source IDs.

    Reads info from file my_sources.txt which is part of package data
    """
    dirs = data_search_dirs()
    ids = []
    for path in dirs:
        try:
            with open(join(path, "my_sources.txt")) as f:
                for line in f:
                    spl = line.split(":")
                    if spl[0].strip().lower() == "name":
                        sid = spl[1].split("#")[0].strip()
                        if sid not in ids:
                            ids.append(sid)
        except IOError:
            pass
    return ids


def get_source_info(source_id, try_online=True):
    """Try access source information from file "my_sources.txt".

    File is part of package data

    :param str source_id: string ID of source (e.g. Etna)
    :param bool try_online: if True and local access fails, try to find source
        ID in online database
    """
    from pyplis import _LIBDIR
    dat = od()
    if source_id == "":
        return dat
    found = 0
    with open(join(_LIBDIR, "data", "my_sources.txt")) as f:
        for line in f:
            if "END" in line and found:
                return od([(source_id, dat)])
            spl = line.split(":")
            if found:
                if not any([line[0] == x for x in["#", "\n"]]):
                    spl = line.split(":")
                    k = spl[0].strip()
                    data_str = spl[1].split("#")[0].strip()
                    dat[k] = data_str
            if spl[0] == "source_ids":
                if source_id in [x.strip()
                                 for x in spl[1].split("#")[0].split(',')]:
                    found = 1
    print("Source info for source %s could not be found" % source_id)
    if try_online:
        try:
            return get_source_info_online(source_id)
        except BaseException:
            pass
    return od()


def get_source_info_online(source_id):
    """Try to load source info from online database (@ www.ngdc.noaa.gov).

    :param str source_id: ID of source
    """
    name = source_id
    name = name.lower()
    url = ("http://www.ngdc.noaa.gov/nndc/struts/results?type_0=Like&query_0="
           "&op_8=eq&v_8=&type_10=EXACT&query_10=None+Selected&le_2=&ge_3="
           "&le_3=&ge_2=&op_5=eq&v_5=&op_6=eq&v_6=&op_7=eq&v_7=&t=102557&s=5"
           "&d=5")
    print("Trying to access volcano data from URL:")
    print(url)
    try:
        # it's a file like object and works just like a file
        data = urlopen(url)
    except BaseException:
        raise

    res = od()
    in_row = 0
    in_data = 0
    lc = 0
    col_num = 10
    first_volcano_name = "Abu"  # this needs to be identical
    ids = ["name", "country", "region", "lat", "lon", "altitude", "type",
           "status", "last_eruption"]
    types = [str, str, str, float, float, float, str, str, str]
    for line in data:
        lc += 1
        if first_volcano_name in line and line.split(">")[1].\
                split("</td")[0].strip() == first_volcano_name:
            in_data, c = 1, 0
        if in_data:
            if c % col_num == 0 and name in line.lower():
                print("FOUND candidate, line: ", lc)
                spl = line.split(">")[1].split("</td")[0].strip().lower()
                if name in spl:
                    print("FOUND MATCH: ", spl)
                    in_row, cc = 1, 0
                    cid = spl
                    res[cid] = od()
            if in_row:
                spl = line.split(">")[1].split("</td")[0].strip()
                res[cid][ids[cc]] = types[cc](spl)
                cc += 1

            if in_row and cc == 9:
                print("End of data row reached for %s" % cid)
                cc, in_row = 0, 0
            c += 1

    return res


def get_icon(name, color=None):
    """Try to find icon in lib icon folder.

    :param str name: name of icon (i.e. filename is <name>.png)
    :param color (None): color of the icon ("r", "k", "g")

    Returns icon image filepath if valid

    """
    try:
        from pyplis import _LIBDIR
    except BaseException:
        raise
    subfolders = ["axialis", "myIcons"]
    for subf in subfolders:
        base_path = join(_LIBDIR, "data", "icons", subf)
        if color is not None:
            base_path = join(base_path, color)
        for file in listdir(base_path):
            fname = basename(file).split(".")[0]
            if fname == name:
                return base_path + file
    print("Failed to load icon at: " + _LIBDIR)
    return False
