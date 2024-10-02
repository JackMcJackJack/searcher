import re
import pandas as pd
import difflib
import sys,os
from collections import Counter
# just need this for function type hinting, could also be solved by upgrading to python3.9+
from typing import List

PrintOn = 1
## NOTE Can't get an incorrect input_search_term like "flat valve" (misheard flap as flat) to detect flap. Tried to do a fuzzy match on the level of words, 
## but didn't really work, and the fuzzy match on the level of letters is returning self cutting isolating valve for some reason
print(".","\n"*8)
# Load database to be searched
search_base_dir = r"C:\Users\jackk\Documents\Maths and Coding\Python\KieranProfit4\Bin Locations\dead databases for matching process\Product_Report_Barcode_Strabaneplumbing.com20240925103014_1761852953908153843.csv"
sb = pd.read_csv(search_base_dir, delimiter='\t', encoding='utf-7',keep_default_na=False)#, engine='python')
# Dropping duplicates so that search_with_search_term(match_type = "ENTIRE WORDS") works properly.
# This should be fine when I have a clean database but double check tk
sb.drop_duplicates(subset = ["Description"])

# Clean artifacts in the column names and data for search base (I think this is redundant now, if you set encoding to be utf-7 instead of utf-8)
#sb.columns = sb.columns.str.replace(r'\+ACI-', '', regex=True)
#sb = sb.replace({r'\+ACI-': '', r'\+ACIAIg-': ''}, regex=True)
# Load database from whence rough descriptions come
description_base_dir = r"C:\Users\jackk\Documents\Maths and Coding\Python\KieranProfit4\Bin Locations\dead databases for matching process\BIN_LOCATION.csv"
db = pd.read_csv(description_base_dir,encoding='utf-7', delimiter='\t', usecols = range(4))[10:20]#, engine='python')
# Clean artifacts in the column names and data for description base
#db.columns = db.columns.str.replace(r'\+ACI-', '', regex=True)
#db = db.replace({r'\+ACI-': '', r'\+ACIAIg-': ''}, regex=True)

test_input = "3/4” non return valve"

def input_to_search_terms(input_search_term : str = test_input,
                        search_term_type : str = "ALPHABETIC WITH SPACES",
                        clean_of_irrelevants : bool = True):
# I feel like making this all one function is a bad coding practice

    ## Generate filters from input

    # Create filter that no search should ever care about (dimensions etc)
    # Note I am making . irrelevant for now, may cause issues later
    irrelevants_pattern = r"(?<=\d)m|.*MM|.*M|.*mm|\sx\s|\dx|\s-|\s{2,}|\.|w "

    # Create standard filters
    double_space_remover = r"\s{2,}"
    number_remover_space_keeper = r"[^a-zA-Z\s]"
    number_keeper = r"[^\d+]" 
    
    if clean_of_irrelevants:
        # Quick clean of the input_search_term to remove irrelevants
        input_search_term = re.sub(irrelevants_pattern,'',input_search_term)

    if search_term_type == "ALPHABETIC WITH SPACES":
        # Remove non-alpha parts and clean the input_search_term
        search_for_alphabetic_parts_with_spaces = re.sub(number_remover_space_keeper,'', input_search_term, flags=re.IGNORECASE).strip()
        search_for_alphabetic_parts_with_spaces = re.sub(double_space_remover,' ', search_for_alphabetic_parts_with_spaces, flags=re.IGNORECASE).strip()
        return search_for_alphabetic_parts_with_spaces
        
    if search_term_type == "NUMBERS":
        # Remove non-numeric parts
        search_for_number_parts = re.sub(number_keeper, '', input_search_term)
        # Number part searches for anything containing all numbers found in the input_search_term
        search_for_number_parts = ''.join([f"(?=.*{number})" for number in search_for_number_parts])
        return search_for_number_parts
    

# SEARCH THE DATABASE FOR ALPHABETIC PARTS
def search_with_search_term(search_term, 
                            search_base=sb,
                            match_type = "DIRECT ENTIRE",
                            cutoff_for_fuzzy_match = .9,
                            num_of_fuzzy_returns = 3):
    if search_base is None:
        print(f"Search base is None, skipping search. Would've searched for '{search_term}'")if PrintOn else None
        return None


    matches = None
    
    if "DIRECT" in match_type:
        if match_type == "DIRECT ENTIRE":
            # Perform case-insensitive search, looking for any entry that contains the entire search term as searched (exactly)
            matches = search_base[search_base['Description'].str.contains(search_term_alphabetic_parts_with_spaces, case=False, na=False)]

        elif match_type == "DIRECT WORDS":
            search_term_split_to_words = search_term_alphabetic_parts_with_spaces.split()
            print(f"Splitting search term and searching individually for {search_term_split_to_words}") if PrintOn else None
            #Gives a list of DataFrames
            matches_as_description_list = [search_with_search_term(search_single_word,
                                                                   search_base, 
                                                                   match_type="DIRECT ENTIRE")
                                           for search_single_word in search_term_split_to_words]
            # Concatenate DataFrames together
            matches_to_single_words_concatenated = pd.concat(matches_as_description_list)
            # Counting number of occurences of each entry (Using 'Reference' is arbitrary)
            number_counts = matches_to_single_words_concatenated['Reference'].value_counts()
            # Keep entry if it shows up more than once
            matches = matches_to_single_words_concatenated[matches_to_single_words_concatenated['Reference'].isin(number_counts[number_counts > 1].index)]
            # Drop duplicates
            matches.drop_duplicates(keep = 'first',inplace= True)
            print(f"When searching for each of {search_term_split_to_words} and keeping only results that show more than once, these are the {len(matches)} results:",matches) if PrintOn else None
        
    elif "FUZZY" in match_type:
        # Need to change get_close_matches so it's case insensitive. Gives more similar results.
        def get_close_matches_case_insensitive(word, possibilities, n=num_of_fuzzy_returns, cutoff=cutoff_for_fuzzy_match):
            # Convert all possibilities to lowercase
            possibilities_upper = [p.upper() for p in possibilities]
            # Get matches from the lowercase version of the word
            matches_lower = difflib.get_close_matches(word.upper(), possibilities_upper, n=n, cutoff=cutoff)
            # Map the lowercase matches back to the original case in the possibilities
            matches = [possibilities[possibilities_upper.index(m)] for m in matches_lower]
            return matches
        if match_type == "FUZZY LETTERS":
            # Uses difflib similarity (gestalt pattern matching apparently) with letters as atoms
            matches_as_description_list = get_close_matches_case_insensitive(search_term_alphabetic_parts_with_spaces, search_base["Description"].to_list(),cutoff=cutoff_for_fuzzy_match, n = num_of_fuzzy_returns)
        elif match_type == "FUZZY WORDS":
            ## DEPRECATED ##
            #I'm going to deprecate this; not returning good results, and better to do an exact search with words as atoms on the exact level
            # Similar to above, but using words as the atoms rather than letters. Will likely be vulnerable to misspellings
            # I could improve this by passing each word to a fuzzy letters search (partially implemented) with a very large num_of_fuzzy_returns
            # and then finding an intersection of both sets. Big cost, and I'm not going to do it now, but could work if still not getting good matches
            search_term_split_to_words = search_term_alphabetic_parts_with_spaces.split()
            matches_as_description_list = [search_with_search_term(search_word,
                                                                   search_base, 
                                                                   cutoff_for_fuzzy_match=cutoff_for_fuzzy_match, 
                                                                   num_of_fuzzy_returns=num_of_fuzzy_returns,
                                                                   match_type="FUZZY LETTERS")
                                           for search_word in search_term_split_to_words]
            # Flattens List
            matches_as_description_list = [x for xs in matches_as_description_list for x in xs ]
            # Removes [] from list
            matches_as_description_list = list(filter(lambda a: a != [], matches_as_description_list))
            
        if (len(matches_as_description_list) == 0) and (cutoff_for_fuzzy_match > 0):
            # Making this very fine, can change later to increase performance
            new_cutoff_for_fuzzy_match = cutoff_for_fuzzy_match *.9
            print(f"No matches found, lower cutoff for similarity to {new_cutoff_for_fuzzy_match:.3}")if PrintOn else None
            return search_with_search_term(search_term_alphabetic_parts_with_spaces, 
                                           search_base,
                                           match_type = match_type,
                                           cutoff_for_fuzzy_match = new_cutoff_for_fuzzy_match, 
                                           num_of_fuzzy_returns = num_of_fuzzy_returns)
        elif cutoff_for_fuzzy_match < 0:
            # This will practically never happen, just including for completeness
            print(f"No matches even at low cutoff_for_fuzzy_match at {cutoff_for_fuzzy_match}")if PrintOn else None
        elif len(matches_as_description_list) > 0:
            # Made search fuzzier until it returned something succesfully
            # Convert back into a dataframe like search_term for forward compatibility
            matches = search_base[search_base['Description'].str.contains('|'.join(matches_as_description_list), case=False, regex=True)]
            print("Found matches debug")if PrintOn else None

    elif match_type == "NUMBERS":

        search_results_number_pass = search_with_search_term(search_term=search_term, search_base=search_base)
        
        return search_results_number_pass
    # Display the matched rows and their indices
    if matches is not None and not matches.empty:
        print(f"Found {len(matches)} matches for '{search_term}':")if PrintOn else None
        if match_type == "FUZZY":
            print(f"(Using similarity cutoff of {cutoff_for_fuzzy_match:.3})")if PrintOn else None
        # Print DataFrame content using to_string()
        print(matches.head().to_string()) if PrintOn else None
        return matches
    else:
        print(f"No match found for '{search_term}'")if PrintOn else None
        return None

def alpha_then_number_search(input_search_term = test_input):
    # Deprecated, job done by match_method_series_search_refiner now
    print(f"** RAW SEARCH TERM : '{input_search_term}' **")if PrintOn else None

    # Perform the first search for alphabetic parts
    print("** FIRST PASS : CHECKING FOR DESCRIPTION ENTIRE TERM MATCH **")if PrintOn else None
    search_term_alphabetic_parts_with_spaces = input_to_search_terms(input_search_term = input_search_term,
                                                                    search_term_type= "ALPHABETIC WITH SPACES", 
                                                                    clean_of_irrelevants=True)

    search_base_alpha_spaced_pass = search_with_search_term(search_term=search_term_alphabetic_parts_with_spaces,
                                                            search_base=sb,
                                                            match_type="DIRECT WORDS")
    pass
    if not isinstance(search_base_alpha_spaced_pass, pd.DataFrame):
        print("** NO RESULTS FOUND : BROADENING SEARCH TO FUZZY MATCH **")if PrintOn else None
        search_base_alpha_spaced_pass = search_with_search_term(search_term=search_term_alphabetic_parts_with_spaces,
                                                                search_base=sb,
                                                                match_type = "FUZZY LETTERS")

    search_term_numbers = input_to_search_terms(input_search_term = input_search_term,
                                                search_term_type= "NUMBERS", 
                                                clean_of_irrelevants=True)
    # If there are matches, perform the second search for numeric parts
    if isinstance(search_base_alpha_spaced_pass, pd.DataFrame):
        
        print("\n\n** SECOND PASS : CHECKING FOR MATCHING DIMENSIONS **") if PrintOn else None

        search_results_number_pass = search_with_search_term(search_term=search_term_numbers, search_base=search_base_alpha_spaced_pass)
        
        return search_results_number_pass
        
        if isinstance(search_results_number_pass, pd.DataFrame):
            if len(search_results_number_pass) == 1:
                #pipeline this into the excel spreadsheet
                pass
            elif len(search_results_number_pass) >1:
                # need to do a thirdpass, or manual review for duplicates
                pass
            elif len(search_results_number_pass) < 1:
                # there are no matches found from the second pass, either manual review or slacken number search requirements to OR rather than AND
                pass
    else:
        
        print(f"No matches found in the first search, skipping the second search. Would've searched for '{search_term_numbers}'") if PrintOn else None
        return pd.DataFrame()

#alpha_then_number_search()

def match_method_series_search_refiner(input_search_term : str = test_input,
                               match_method_series : List[str] = ["DIRECT ENTIRE"],
                               init_search_base = sb):

    print(f"** RAW SEARCH TERM : '{input_search_term}' **")if PrintOn else None
    # Initialise search results
    search_results = pd.DataFrame()
    # Initialise search base
    search_base = init_search_base
    # Start attempt, with method
    for attempt_number,match_method in enumerate(match_method_series):
        print(f"** ATTEMPT NUMBER {attempt_number+1}: USING METHOD \"{match_method}\"") if PrintOn else None
        if not "NUMBERS" in match_method_series:
            search_term = input_to_search_terms(input_search_term = input_search_term,
                                                                search_term_type= "ALPHABETIC WITH SPACES", 
                                                                clean_of_irrelevants=True)
        else:
            search_term = input_to_search_terms(input_search_term = input_search_term,
                                            search_term_type= "NUMBERS", 
                                            clean_of_irrelevants=True)
            
        # Apply method to search base, return search_results using that method
        search_results = search_with_search_term(search_term=search_term,
                                                search_base= search_base,
                                                match_type=match_method)
        # If that method refined the search base to nothing, skip it and try the next one
        if search_results.empty:
            print("No search results found for this method, continuing to next method") if PrintOn else None
        # If it refined successfully to one or more entry, make the results the new base and move to next refinement method
        else:
            search_base = search_results
    print(f"After applying {' then, '.join(match_method_series)}, these are the {len(search_results)} search results found for \"{input_search_term}\":\n",search_results) if PrintOn else None
    return search_results

def match_from_description_database_to_search_database():
    for index, row in db.iterrows():
        physical_description = row["Product Physical Description"]
        if pd.notna(physical_description):
            search_results_from_physical_description = alpha_then_number_search(physical_description)
            if search_results_from_physical_description is not None:
                #Just selecting top result for now
                search_results_from_physical_description = search_results_from_physical_description.head(1)
                db.at[index,"Matched Product Description from stock take"] = search_results_from_physical_description["Description"].iloc[0]
                db.at[index,"Matched Product ID from stock take"] = search_results_from_physical_description["Reference"].iloc[0]
            else:
                db.at[index,"Matched Product Description from stock take"] = "No Product Found"
                db.at[index,"Matched Product ID from stock take"] = "No Product Found"
        else:
            db.at[index,"Matched Product Description from stock take"] = "No Phys Desc given"
            db.at[index,"Matched Product ID from stock take"] = "No Phys Desc given"
    db.to_csv(r"C:\Users\jackk\Documents\Maths and Coding\Python\KieranProfit4\Bin Locations\dead databases for matching process\result.csv",
              sep = "\t",
              mode = 'w',
              encoding='utf-7')

#sys.stdout = open(os.devnull, 'w')
#match_from_description_database_to_search_database()
#alpha_then_number_search(test_input)
match_method_series_search_refiner(input_search_term = test_input,
                           match_method_series= ["DIRECT WORDS","NUMBERS"],
                           init_search_base=sb)