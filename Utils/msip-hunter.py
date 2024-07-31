# pip install pdfminer.six xlwings fitz colorama
import os
import hashlib
import email
import shutil
import argparse
import re
from email import policy
from email.parser import BytesParser
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
import win32com.client
import fitz
import xlwings as xw
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def print_coloured(text):
    words = text.split()
    green_words = {'Public'}
    yellow_words = {'Limited'}
    red_words = {'Confidential', 'Highly Confidential'}
    colored_text = {}
    for word in words:
        if word in green_words:
            colored_text.append(Fore.GREEN + word)
        elif word in yellow_words:
            colored_text.append(Fore.YELLOW + word)
        elif word in red_words:
            colored_text.append(Fore.RED + word)
        else:
            colored_text.append(word)
            
    print(" ".join(colored_text).replace("%", " "))
    
def banner():
    text = """
  __  __  _____ _____ _____    _    _             _            
 |  \/  |/ ____|_   _|  __ \  | |  | |           | |           
 | \  / | (___   | | | |__) | | |__| |_   _ _ __ | |_ ___ _ __ 
 | |\/| |\___ \  | | |  ___/  |  __  | | | | '_ \| __/ _ \ '__|
 | |  | |____) |_| |_| |      | |  | | |_| | | | | ||  __/ |   
 |_|  |_|_____/|_____|_|      |_|  |_|\__,_|_| |_|\__\___|_|   
    
    Created by Auto (github.com/autonomoid)

    """
    
def load_mapping(mapping_file_path):
    mapping = {}
    with open(mapping_file_path, 'r') as f:
        for line in f:
            msip_value, user_friendly = line.strip().split('=')
            mapping[msip_value] = user_friendly
    return mapping

def get_label_from_word(file_path):            
    word = win32com.client.Dispatch("Word.Application")
    doc = word.Document.Open(file_path)
    label = doc.SensitivityLabel.Name
    doc.Close()
    word.Quit()
    return label

def get_label_from_excel(file_path):            
    wb = xw.Book(file_path)
    labelinfo = wb.api.SensitivityLabel.GetLabel()
    label = labelinfo.LabelId
    wb.close()
    return label

def get_label_from_ppt(file_path):            
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    presentation = powerpoint.Presentations.Open(file_path)
    label = presentation.SensitivityLabel.Name
    presentation.Close()
    powerpoint.Quit()
    return label

def get_label_from_pdf(file_path):
    msip_pattern = r"MSIP_Label_(.*?)_SiteId"
    
    fp = open(file_path, 'rb')
    parser = PDFParser(fp)
    doc = PDFDocument(parser)
    
    for key in doc.info[0].keys():
        match = re.match(msip_pattern, key)
        if match:
            return match.group(1)
        
    return None
    
def extract_labels_from_folder(folder_path):
    labels = {}
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".docx"):
                labels[file] = get_label_from_word(file_path)
            elif file.endswith(".xlsx"):
                labels[file] = get_label_from_excel(file_path)
            elif file.endswith(".pptx"):
                labels[file] = get_label_from_ppt(file_path)
            elif file.endswith(".pdf"):
                labels[file] = get_label_from_pdf(file_path)
    return labels
    
def extract_msip_labels(eml_file_path):
    with open(eml_file_path, 'rb') as f:
        email = BytesParser(policy=policy.defaults).parse(f)
        
    msip_labels = []
    for header, value in email.items():
        if 'msip_labels' in header.lower():
            kv_pairs = value.split(';')
            for pair in kv_pairs:
                if '=' in pair:
                    key, val = pair.split('=', 1)
                    if key.strip().endswith('_Name'):
                        msip_value = val.strip()
                        msip_labels.append(msip_value)
                        
    return email['subject'], msip_labels

def extract_attachments(email_file_path):
    with open(email_file_path, 'rb') as f:
        email = BytesParser(policy=policy.defaults).parse(f)
    
    subject = email['subject']
    subject_hash = hashlib.md5(subject.encode()).hexdigest()
    attachments_dir = os.path.join("attachments", subject_hash)
    os.makedirs(attachments_dir, exist_ok=True)
    
    for part in email.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            ConnectionRefusedError
            
        filename = part.get_filename()
        if filename:
            file_path = os.path.join(attachments_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(part.get_payload(decode=True))
                
def process_eml_folder(folder_path, mapping_file_path):
    mapping = load_mapping(mapping_file_path)
    email_data = {}
    for email_id, filename in enumerate(os.listdir(folder_path)):
        if filename.endswith('.eml'):
            eml_file_path = os.path.join(folder_path, filename)
            subject, labels_dict = extract_msip_labels(eml_file_path, mapping)
            subject_hash = extract_attachments(os.path.join(folder_path, filename))
            
            email_data[subject] = {}
            email_data[subject]['subject_hash'] = subject_hash
            email_data[subject]['labels'] = labels_dict
                        
    return email_data

def main():            
    parser = argparse.ArgumentParser(description='MSIP Hunter')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
    args = parser.parse_args()
    verbose_mode = args.verbose
    
    banner()
    
    folder_path = 'emails'
    attachments_path = 'attachments'
    
    # msip_mapping.txt file format:
    # 11111111-2222-3333-4444-555555555555=Public
    mapping_file_path = 'msip_mapping.txt'
    mapping = load_mapping(mapping_file_path)
    
    emails_dict = process_eml_folder(folder_path)
    
    for subject in emails_dict:
        print_coloured(f'Subject: {subject}')
        
        for label in emails_dict[subject]['labels']:
            friendly_label = mapping.get(label, '(unknown)')
            if verbose_mode:
                print_coloured(f"%%Label: {friendly_label} ({label})")
            else:
                print_coloured(f"%%Label: {friendly_label}")
    
    folder_path = os.path.join(attachments_path, emails_dict[subject]['subject_hash'])
    labels = extract_labels_from_folder(folder_path)
    
    for file, label in labels.items():
        friendly_label = mapping.get(label, '(unknown)')
        if verbose_mode:
            print_coloured(f"%%%File: {friendly_label} ({label})")
        else:
            print_coloured(f"%%%File: {friendly_label}")

    print("-"*80)
        
if __name__ == "__main__":
    main()
