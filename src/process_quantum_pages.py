"""Script for parsing quantum fiber html files"""
# import statements
import os
from lxml import etree
import pandas as pd

def parse_quantum_page_from_folder(directory_path: str, outfile: str, file_type: str='txt'):
    """
    Parse quantum fiber html pages from a directory
    :param directory_path: relative path to directory containing html files
    :type directory_path: str
    :param outfile: relative path to file to write to
    :type outfile: str
    :param file_type: file extension
    :type file_type: str
    :returns: None
    """
    pages_dir_path = directory_path
    if not os.path.exists(pages_dir_path): # confirm path to directory exists
        raise FileNotFoundError
    if not os.path.exists(outfile): # confirm path to outfile exists
        raise FileNotFoundError
    file_names = os.listdir(pages_dir_path) # collect file names
    headers = None
    raw_data = []
    i = 0
    for n in file_names: # parse all files
        i += 1
        print(f'parsing {i} of {len(file_names)}: {n}')
        if not headers:
            rows, headers = parse_quantum_page(
                path=pages_dir_path, file_name=n, file_type=file_type, get_headers=True)
            raw_data.extend(rows)
        else:
            rows = parse_quantum_page(path=pages_dir_path, file_name=n, file_type=file_type)
            raw_data.extend(rows)
    outdata = pd.DataFrame(data=raw_data, columns=headers)
    outdata.to_csv(outfile, index=False)

def parse_quantum_page(path, file_name, file_type: str, get_headers=False):
    """
    Parse quantum fiber html page
    Assumes that the file is parsable by lxml
    :param path: relative path to file
    :type path: str
    :param file_name: name of file
    :type file_name: str
    :param file_type: file extension
    :type file_type: str
    :param get_headers: whether to return headers
    :type get_headers: bool
    :returns: row(s) contain relevant data (from data-pid div)
    :rtype: list of lists
    """
    headers = None
    rows = []
    with open(file='/'.join((path, file_name)), encoding='utf-8', mode='r') as f:
        q_text = f.read()
        html_root = etree.fromstring(text=q_text, parser=etree.HTMLParser())
        # find the data tag
        data = html_root.xpath("//div[@data-pid]")
        if data:
            headers = ['address'] + list(data[0].attrib.keys())
        for el in data: # a file may have multiple data tags
            row = []
            row.append(file_name[:-(1 + len(file_type))]) # add address from file name
            # extract data
            d = el.attrib
            for key in d.keys():
                row.append(d[key])
            rows.append(row)
    if get_headers:
        return (rows, headers)
    return rows

if __name__ == '__main__':
    parse_quantum_page_from_folder(
        directory_path='../data_out/quantum_pages',
        outfile='../data_out/quantum_pages.csv'
    )
