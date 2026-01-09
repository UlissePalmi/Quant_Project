from risk_factor_pred.core import secDownloader as sd, htmlCleaner
from risk_factor_pred.consts import SEC_DIR

def find_ciks():
    ciks = [cik.name for cik in SEC_DIR.iterdir()]
    print(ciks)
    return ciks


if __name__ == "__main__":
    
    # Create list of ciks from excel file or request cik in input
    ciks = find_ciks() if sd.inputLetter() == 'l' else [input("Enter CIK...").upper()]
    
    # Remove HTML tags from previously created list
    for cik in ciks:
        htmlCleaner.cleaner((cik), output_filename = "full-submission.txt")