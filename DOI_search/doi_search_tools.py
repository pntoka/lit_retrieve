"""
Functions to retrieve DOIs using semantic scholar API
"""

import requests
import time
import os
import tomllib


def sem_scholar_bulk(query, pub_dates, use_token=False):
    """
    Function that takes a query and pub dates and does a bulk search for DOIs
    returns json of API response
    """
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
    headers = {"content-type": "application/json"}
    params = {
        "query": "{query}".format(query=query),
        "year": "{year}".format(year=pub_dates),
        "limit": 1000,
        "fields": "externalIds,publicationTypes",
    }
    if use_token is not False:
        params.update({"token": use_token})
    response = requests.get(base_url, headers=headers, params=params)
    count = 0
    while response.status_code != 200:
        print(
            "Error: "
            + str(response.status_code)
            + " trying request again, attempt "
            + str(count + 1)
        )
        time.sleep(30)
        response = requests.get(base_url, headers=headers, params=params)
        count += 1
        if count == 10:
            break
    print(
        "Request successful for pub date = {pub_dates} and query = {query}".format(
            pub_dates=pub_dates, query=query
        )
    )
    data = response.json()
    return data


def bulk_search_doi_pubtype(query, pub_dates):
    """
    Function that takes a query and pub dates and returns a dict of DOIs and pubtypes
    """
    data = sem_scholar_bulk(query, pub_dates)
    doi_dict = {}
    for paper in data["data"]:
        if "DOI" in paper["externalIds"]:
            doi_dict[paper["externalIds"]["DOI"]] = paper["publicationTypes"]
    while data["token"] is not None:
        data = sem_scholar_bulk(query, pub_dates, data["token"])
        for paper in data["data"]:
            if "DOI" in paper["externalIds"]:
                doi_dict[paper["externalIds"]["DOI"]] = paper["publicationTypes"]
        time.sleep(1)
    return doi_dict


def doi_dict_filter(doi_dict, pub_type, pub_skip):
    """
    Function that takes a doi dictionary and a publication type and returns
    a list of DOIs that match the publication type without the publication type to skip
    """
    doi_list = []
    if pub_type is None:
        for doi in doi_dict.items():
            doi_list.append(doi)
        return doi_list
    for doi, pub_types in doi_dict.items():
        if pub_types is None:
            doi_list.append(doi)
        elif pub_type in pub_types and pub_skip not in pub_types:
            doi_list.append(doi)
    return doi_list


def storeDOI(dois, save_dir):  # Function to save list of dois to file
    with open(os.path.join(save_dir, "doi_all.txt"), "a", encoding="utf-8") as save_file:
        for doi in dois:  # saves dois to doi.txt file with each doi on new line
            save_file.write(doi + "\n")


def get_dois_sem_sch(query, pub_dates, save_dir, pub_type=None, pub_skip=None):
    """
    Function that take a query and pub dates and saves in a file the DOIs found
    """
    doi_dict = bulk_search_doi_pubtype(query, pub_dates)
    doi_list = doi_dict_filter(doi_dict, pub_type, pub_skip)
    storeDOI(doi_list, save_dir)


def doi_search(query_list, pub_dates, save_dir, pub_type=None, pub_skip=None):
    """
    Function that takes a list of queries, a range of ublication dates and a directory to save the results
    and returns a list of DOIs in a file. Results for each query are saved in a different directory
    """
    for query in query_list:
        save_dir_results = os.path.join(save_dir, list(query.keys())[0])
        os.mkdir(save_dir_results)
        get_dois_sem_sch(list(query.values())[0], pub_dates, save_dir_results, pub_type, pub_skip)
        with open(os.path.join(save_dir_results, f"{list(query.keys())[0]}.txt"), "w", encoding="utf-8") as f:
            f.write(list(query.values())[0])
        time.sleep(5)


def doi_unique(query_list, save_dir):
    """
    Function that goes through search results for different queries and returns a list of unique DOIs that is saved in a file
    """
    doi_list = []
    for query in query_list:
        folder = os.path.join(save_dir, list(query.keys())[0])
        if os.path.exists(os.path.join(folder, "doi_all.txt")) is False:
            continue
        else:
            with open(os.path.join(folder, "doi_all.txt"), "r", encoding="utf-8") as file:
                dois = file.read().splitlines()
            doi_list.extend(dois)
    doi_list_unique = list(
        set(doi_list)
    )  # removes duplicates and leaves only unique dois
    with open(os.path.join(save_dir, "doi_unique.txt"), "a", encoding="utf-8") as save_file:
        for (
            doi
        ) in doi_list_unique:  # saves dois to doi.txt file with each doi on new line
            save_file.write(doi + "\n")


def parse_query(query_file):
    with open(query_file, "rb") as file:
        query_data = tomllib.load(file)
    
    pub_dates = str(query_data["pub_dates"]['start']) + "-" + str(query_data["pub_dates"]['end'])
    search_queries = [{key: query_data["queries"][key]} for key in query_data["queries"] if key.startswith('query')]
    # for i in range(query_numbers):
    #     search_queries.append(query_data["queries"][f'query_{i+1}'])
    save_dir = query_data["save_dir"]['folder_path']
    if "pub_types" not in query_data or "pub_type" not in query_data["pub_types"]:
        pub_type = None
        pub_skip = None
    pub_type = query_data["pub_types"]['pub_type']
    pub_skip = query_data["pub_types"]['pub_skip']
    if "prefixes" not in query_data or 'prefix_list' not in query_data["prefixes"]:
        prefix_list = None
    else:
        prefix_list = query_data["prefixes"]['prefix_list']
    if query_data["search_engine"]['crossref']:
        engine = 'crossref'
    elif query_data["search_engine"]['semantic_scholar']:
        engine = 'semantic_scholar'
    return pub_dates, search_queries, save_dir, pub_type, pub_skip, prefix_list, engine

    # with open(query_file, "r") as file:
    #     query_list = file.read().splitlines()
    # pub_dates = query_list[0].split(" ")
    # pub_dates = pub_dates[0] + "-" + pub_dates[1]
    # search_queries = query_list[1:]
    # return pub_dates, search_queries


def parse_args(args):
    """
    Function to parse command line arguments
    """
    query_file = args[0]
    pub_dates, query_list, save_dir, pub_type, pub_skip, prefix_list, engine = parse_query(query_file)
    return pub_dates, query_list, save_dir, pub_type, pub_skip, prefix_list, engine


def filter_dois(file, prefixes, save_dir):
    """
    Function to filter DOIs from a file
    """
    with open(os.path.join(save_dir, file), "r", encoding="utf-8") as f:
        dois = f.read().splitlines()
    filtered_dois = []
    for doi in dois:
        for prefix in prefixes:
            if doi.startswith(prefix):
                filtered_dois.append(doi)
    with open(os.path.join(save_dir, "dois_select.txt"), "a", encoding="utf-8") as f:
        for doi in filtered_dois:
            f.write(doi + "\n")


def crossref_search(
    pub_date, query, prefix, pub_type="journal-article", use_cursor="*"
):
    """
    Function to search crossref for journal article DOIs from specified prefix and publication date
    """
    pub_date = pub_date.split("-")
    base_url = "https://api.crossref.org/prefixes/{prefix}/works"
    headers = {"Accept": "application/json"}
    params = {
        "filter": f"from-pub-date:{pub_date[0]},until-pub-date:{pub_date[1]},type:{pub_type}",
        "rows": 1000,
        "query": query,
        "select": "DOI",
        "cursor": use_cursor,
    }
    if use_cursor != "*":
        params.update({"cursor": use_cursor})
    response = requests.get(
        base_url.format(prefix=prefix), headers=headers, params=params
    )
    data = response.json()
    if data["status"] == "ok":
        print(
            "Request successful for pub date = {pub_dates} and query = {query} and prefix = {prefix}".format(
                pub_dates=pub_date, query=query, prefix=prefix
            )
        )
    return data


def crossref_search_paging(pub_date, query, prefix, pub_type="journal-article"):
    """
    Function to search crossref for journal article DOIs from specified prefix and publication date
    """
    data = crossref_search(pub_date, query, prefix, pub_type)
    all_dois = []
    if data["status"] == "ok":
        all_dois.extend(
            [doi for doi_dict in data["message"]["items"] for doi in doi_dict.values()]
        )
        if len(data["message"]["items"]) < 1000:
            return all_dois
        else:
            cursor = data["message"]["next-cursor"]
            while cursor != "*":
                data = crossref_search(pub_date, query, prefix, pub_type, cursor)
                all_dois.extend(
                    [
                        doi
                        for doi_dict in data["message"]["items"]
                        for doi in doi_dict.values()
                    ]
                )
                if len(data["message"]["items"]) < 1000:
                    return all_dois
                else:
                    cursor = data["message"]["next-cursor"]


def get_dois_crossref(query, pub_dates, save_dir):
    """
    Function that takes a query and pub dates and saves in a file the DOIs found
    """
    prefixes = [
        "10.1016",
        "10.1021",
        "10.1039",
        "10.1002",
        "10.1007",
        "10.1080",
        "10.1038",
    ]
    doi_list_all = []
    for prefix in prefixes:
        doi_list = crossref_search_paging(pub_dates, query, prefix)
        doi_list_all.extend(doi_list)
    storeDOI(doi_list_all, save_dir)


def doi_search_crossref(query_list, pub_dates, save_dir):
    """
    Function that takes a list of queries, a range of ublication dates and a directory to save the results
    and returns a list of DOIs in a file. Results for each query are saved in a different directory
    """
    for i, query in enumerate(query_list):
        save_dir_results = os.path.join(save_dir, f'query_{i+1}')
        os.mkdir(save_dir_results)
        get_dois_crossref(list(query.values())[0], pub_dates, save_dir_results)
        with open(os.path.join(save_dir_results, f"query_{i+1}.txt"), "w", encoding="utf-8") as f:
            f.write(list(query.values())[0])
        time.sleep(5)
