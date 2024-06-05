from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta
from elasticsearch_dsl import Q, AttrList, Date
from elasticsearch_dsl import Search
import elasticsearch_dsl
from elasticsearch_dsl.connections import connections
from elasticsearch.helpers import bulk

def retrieve_non_empty_texts_dates(index: str, 
                                   user_id=None, 
                                   mention=None, 
                                   source=None, 
                                   market_analysis_date=None) -> list:
    
    # Create a base search object
    s = Search(index=index)
    
    # Create a list to hold our should query components
    query_components = []

    # If specific values are provided, add them under the should conditions
    if user_id:
        query_components.append(Q('match', user_id=user_id))
    if mention:
        query_components.append(Q('match', mention=mention))
    if source:
        query_components.append(Q('match', source=source))
    if market_analysis_date:
        query_components.append(Q('match', market_analysis_date=market_analysis_date))

    # Add the conditions for non-empty mentions_texts or hashtags_texts
    query_components.append(Q('exists', field='mentions_texts'))
    query_components.append(Q('exists', field='hashtags_texts'))

    # Construct the final query
    s = s.query('bool', 
                should=query_components,
                minimum_should_match=1)  # At least one should condition must be met
    
    # Only fetch the date field
    s = s.source(includes=["date"])

    # Execute the search and return the results
    response = s.execute()
    # print(s.to_dict())   # This will print the actual query being sent to Elasticsearch
    # print(response.hits.total) 

    # Extract dates from the response
    dates = [hit.date for hit in response.hits if hasattr(hit, 'date')]
    return dates

def add_percentage_sign(percentage: float) -> str:
    str_percentage = f"{percentage}%"

    if percentage > 0:
        str_percentage = f"+{percentage}%"

    return str_percentage

def normalize_percentage(value : float) -> float:

    percentage = round(value, 4)
    int_percentage = int(percentage)
    # If the percentage is an integer example 50.00
    if percentage == int_percentage:
        # Remove decimal places
        percentage = int_percentage

    return percentage

def advanced_percentage_count(previous_interval_total: int,
                              current_interval_total: int,
                              null: str) -> str:
    if previous_interval_total == current_interval_total:
        str_interval_percentage = null
    else:
        # If previous interval total is positive
        if previous_interval_total > 0:

            if current_interval_total > 0:
                percentage_value = (
                    (current_interval_total - previous_interval_total)
                    / previous_interval_total)
            else:
                percentage_value = \
                    current_interval_total - previous_interval_total

            interval_percentage = normalize_percentage(percentage_value * 100)

            str_interval_percentage = add_percentage_sign(interval_percentage)
        else:
            # If previous interval total is 0
            str_interval_percentage = f"+{current_interval_total*100}%"

    return str_interval_percentage

def hashtags_mentions_count(mentions_fields: list,
                            index: str,
                            user_id: str,
                            mention: str,
                            recent_market_analysis_date : str,
                            source=None,
                            start_date=None,
                            end_date=None) -> int:
    print(f"Start date: {start_date}, End date: {end_date}")

    total_mentions_nbr = 0

    for mention_field in mentions_fields:
        if source is not None:
            if start_date is not None and end_date is not None:
                mentions = fields_values(
                    index,
                    mention_field,
                    start_date=start_date,
                    end_date=end_date,
                    user_id=user_id,
                    mention=mention,
                    source=source,
                    market_analysis_date=recent_market_analysis_date)
            else:
                mentions = fields_values(
                    index,
                    mention_field,
                    user_id=user_id,
                    mention=mention,
                    source=source,
                    market_analysis_date=recent_market_analysis_date)
        else:
            mentions = fields_values(
                index,
                mention_field,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id,
                mention=mention,
                market_analysis_date=recent_market_analysis_date)

        if mentions is not None:
            for mnt in mentions:
                total_mentions_nbr += getattr(mnt, mention_field)

    return total_mentions_nbr

def unique_field_values(index: str,
                        field: str,
                        start_date=None,
                        end_date=None,
                        **kwargs) -> list:
    print("start date in unique fields value", start_date)
    print("end date in unique fields value", end_date)
    unique = []

    verif = start_date is not None and end_date is not None

    if verif:
        total_documents = search_total(index,
                                       start_date=start_date,
                                       end_date=end_date,
                                       **kwargs)
    else:
        total_documents = search_total(index, **kwargs)

    if total_documents != 0:
        try:
            s = Search(index=index)
            query_list = [{"match": {key: value}} for key, value in kwargs.items()]
            s = s.query("bool",
                        should=query_list,
                        minimum_should_match=len(kwargs))
            if verif:
                s = s.filter("range", date={"gte": start_date,
                                            "lte": end_date})
            s.aggs.bucket("unique",
                        "terms",
                        field=field,
                        size=total_documents)
            response = s.execute()
            unique = [bucket for bucket in response.aggregations.unique.buckets]
        except Exception as e:
            print(f"Error during Elasticsearch operations: {e}")
    return unique

def fields_values(index: str,
                  fields: str,
                  start_date=None,
                  end_date=None,
                  delete=False,
                  classes_length=None,
                  **kwargs) -> elasticsearch_dsl.response:

    result = None
    verif = start_date is not None and end_date is not None

    if not verif:
        total_documents = search_total(index,
                                       start_date=start_date,
                                       end_date=end_date,
                                       **kwargs)
    else:
        total_documents = search_total(index, **kwargs)

    if total_documents != 0:
        s = Search(index=index)
        query_list = [{"match": {key: value}} for key, value in kwargs.items()]
        s = s.query("bool",
                    should=query_list,
                    minimum_should_match=len(kwargs))
        if verif:
            s = s.filter("range", date={"gte": start_date,
                                        "lte": end_date})
        s = s.source(fields=fields)
        # s = s.sort({"market_analysis_date": {"order": "desc"}})
        s = s.extra(size=total_documents)
        result = s.execute() 
        # if fields == "text":
        #     result = [hit.text for hit in result.hits]
    if classes_length and delete and result is not None:
        if "classes" in result[0] and hasattr(result[0].classes, '__len__') \
           and classes_length != len(result[0].classes):
            s.delete()
        else:
            return result

    elif delete and result and classes_length is None:
        s.delete()
    # print("hashtags texts and mentions texts included", result)
    return result

def get_dates_by_range(index,user_id,start_date,end_date,market_analysis_date,existing_fields):
    s = Search(index=index)
    query_components = []
    # If specific values are provided, add them under the should conditions
    if user_id:
        query_components.append(Q('match', user_id=user_id))
    if market_analysis_date:
        query_components.append(Q('match', market_analysis_date=market_analysis_date))
        
    for field in existing_fields:
        query_components.append(Q('exists', field=field))    

    s = s.filter("range", date={"gte": start_date,"lte": end_date})
    
    s = s.query('bool', should=query_components,minimum_should_match=1)
    
    s = s.source(includes=["date"])

    response=s.execute()

    dates=[hit.date for hit in response.hits if(hasattr(hit,'date'))]
    for hit in response.hits:
        if(hasattr(hit,'market_analysis_date')):
            print(f"market analysis date is {hit.market_analysis_date}") 
    return dates

def months_chart(index: str,
                start_month: str,
                end_month: str,
                user_id: str,
                mention: str,
                sources: list,
                colors: list,
                y_m_format: str,
                y_m_dT00_00_format: str,
                y_m_dT23_59_format: str,
                mentions_fields: list,
                author_field : str,
                null: str,
                recent_market_analysis_date : str,
                capitalized_sources : list,
                filtered_documents=None) -> dict:

    if not start_month:
        return {
            "message": "Kindly select a date range to display results."
        }
    parts1=start_month.split('-')
    if(len(parts1)==2 and end_month):# years
        parts2=end_month.split('-')
        main_start_date=datetime.strptime(f"{parts1[0]}-{parts1[1]}","%Y-%m")
        print("main start date", main_start_date)
        main_end_date=datetime.strptime(f"{parts2[0]}-{parts2[1]}","%Y-%m")
        print("main end date", main_end_date)
        interval_length=relativedelta(months=1)
        print("interval_length", interval_length)

    elif(len(parts1)==2 and not end_month):# month
        main_start_date=datetime.strptime(f"{parts1[0]}-{parts1[1]}","%Y-%m")
        main_end_date=main_start_date+relativedelta(months=1)
        interval_length=relativedelta(days=7)

    elif(len(parts1)==3):# day
        main_start_date=datetime.strptime(f"{parts1[0]}-{parts1[1]}-{parts1[2]}","%Y-%m-%d")
        main_end_date=main_start_date+relativedelta(days=1)
        interval_length=relativedelta(hours=1)

    elif(len(parts1)>=5 and end_month): # week
        parts2=end_month.split('-')
        main_start_date = datetime.strptime(f"{parts1[0]}-{parts1[1]}-{parts1[2]}", "%Y-%m-%d")
        print("main start date", main_start_date)
        main_end_date=datetime.strptime(f"{parts2[0]}-{parts2[1]}-{parts2[2]}","%Y-%m-%d")
        print("main end date", main_end_date)
        interval_length=relativedelta(days=1)
        print("interval_length", interval_length)
    else:
        return {"error":"invalid date selected","status":400}
    
    date_format = '%Y-%m-%dT%H:%M'

    months_chart_dict = {}
    # verif = not end_month or start_month < end_month

    # if verif:

    periods = []
    final_dates = []
    start_dates = []
    end_dates = []
    total_unique_authors = []
    total_mentions = []
    sources_total_unique_authors = []
    sources_total_mentions = []
    sources_total_hashtags = []
    total_mentions_percentages = []
    total_unique_authors_percentages = []

    texts_dates = set()
    for source in sources:
            relevant_dates = retrieve_non_empty_texts_dates(
                index,
                user_id=user_id,
                mention=mention,
                source=source,
                market_analysis_date=recent_market_analysis_date
            )
            texts_dates.update(relevant_dates)
    while main_start_date < main_end_date:
        periods.append(main_start_date)
        print(f"Adding period: {main_start_date.strftime(date_format)}")  # Print the period being added
        main_start_date += interval_length

    #periods.insert(0, main_start_date)
    # periods.sort()

    nbr_intervals = len(periods)
    print(f"Number of intervals: {nbr_intervals}")
    for i in range(nbr_intervals):
        date = periods[i]
        current_start_date_str = date.strftime(date_format)
        current_end_date_str = (date + interval_length - relativedelta(minutes=1)).strftime(date_format)
        start_dates.append(current_start_date_str)  
        end_dates.append(current_end_date_str)
        print(f"Interval {i+1}: Start Date: {current_start_date_str}, End Date: {current_end_date_str}")
    if filtered_documents is not None:
        total_mentions_nbr = sum(1 for doc in filtered_documents if doc['mention'] == mention)
    else:
        total_mentions_nbr = search_total(
            index,
            mention=mention,
            user_id=user_id,
            market_analysis_date=recent_market_analysis_date)
    if total_mentions_nbr:
        for i in range(nbr_intervals):
            date_start = start_dates[i]
            print("dates start in the second loop", date_start)
            date_end = end_dates[i]
            print("dates end in the second loop", date_end)
            interval_total_unique_authors = []
            interval_total_mentions = []
            interval_dates = []
            interval_total_hashtags = []
            interval_authors = 0


            if filtered_documents is not None:
                unique_authors = set()
                for doc in filtered_documents:
                    date_start_datetime = datetime.strptime(date_start, date_format)
                    date_end_datetime = datetime.strptime(date_end, date_format)
                    doc_date = datetime.strptime(doc['date'], date_format)
                    if date_start_datetime <= doc_date <= date_end_datetime:
                        unique_authors.add(doc['author'])
            else:
                unique_authors = unique_field_values(
                    index,
                    author_field,
                    start_date=date_start,
                    end_date=date_end,
                    mention=mention,
                    user_id=user_id,
                    market_analysis_date=recent_market_analysis_date)

            if unique_authors:
                interval_authors = len(unique_authors)

            total_unique_authors.append(interval_authors)

            if i == 0:
                str_interval_percentage = null
            else:
                str_interval_percentage = advanced_percentage_count(
                    total_unique_authors[i - 1],
                    total_unique_authors[i],
                    null)
            total_unique_authors_percentages.\
                append(str_interval_percentage)
            
            if filtered_documents is not None:
                interval_mentions = 0

                for doc in filtered_documents:
                    date_start_datetime = datetime.strptime(date_start, date_format)
                    date_end_datetime = datetime.strptime(date_end, date_format)
                    doc_date = datetime.strptime(doc['date'], date_format)
                    if doc['mention'] == mention and date_start_datetime <= doc_date <= date_end_datetime:
                        interval_mentions += 1
            else:
                interval_mentions= hashtags_mentions_count(
                    mentions_fields,
                    index,
                    user_id,
                    mention,
                    recent_market_analysis_date,
                    start_date=date_start,
                    end_date=date_end)

            total_mentions.append(interval_mentions)
            
            if i == 0:
                str_interval_percentage = null
            else:
                str_interval_percentage = advanced_percentage_count(
                    total_mentions[i - 1],
                    total_mentions[i],
                    null)

            total_mentions_percentages.append(str_interval_percentage)

            for source in sources:
                source_total_unique_authors_nbr = 0
                unique_authors_per_source = set()
                
                if filtered_documents is not None:
                    for doc in filtered_documents:
                        date_start_datetime = datetime.strptime(date_start, date_format)
                        date_end_datetime = datetime.strptime(date_end, date_format)
                        doc_date = datetime.strptime(doc['date'], date_format)
                        if doc['source'] == source and date_start_datetime <= doc_date <= date_end_datetime:
                            # source_total_unique_authors_nbr += 1
                            unique_authors_per_source.add(doc['author'])
                    source_total_unique_authors_nbr = len(unique_authors_per_source)
                else:
                    source_unique_authors = unique_field_values(
                        index,
                        author_field,
                        start_date=date_start,
                        end_date=date_end,
                        mention=mention,
                        user_id=user_id,
                        source=source,
                        market_analysis_date=recent_market_analysis_date)

                    if source_unique_authors:
                        source_total_unique_authors_nbr = len(
                            source_unique_authors)

                interval_total_unique_authors.append(
                    source_total_unique_authors_nbr)
                if filtered_documents is not None:
                    source_total_mentions_nbr = 0
                    for doc in filtered_documents:
                        date_start_datetime = datetime.strptime(date_start, date_format)
                        date_end_datetime = datetime.strptime(date_end, date_format)
                        doc_date = datetime.strptime(doc['date'], date_format)
                        if doc['mention'] == mention and doc['source'] == source and date_start_datetime <= doc_date <= date_end_datetime:
                            source_total_mentions_nbr += 1
                else:
                    source_total_mentions_nbr = hashtags_mentions_count(
                        mentions_fields,
                        index,
                        user_id,
                        mention,
                        recent_market_analysis_date,
                        source=source,
                        start_date=date_start,
                        end_date=date_end)
                
                interval_total_mentions.append(source_total_mentions_nbr)
            sources_total_unique_authors.append(interval_total_unique_authors)
            sources_total_mentions.append(interval_total_mentions)
            sources_total_hashtags.append(interval_total_hashtags)
            interval_dates.append(final_dates)
    months_chart_dict["months"] = periods
    months_chart_dict["colors"] = colors
    months_chart_dict["sources"] = capitalized_sources
    months_chart_dict["total_mentions"] = total_mentions
    months_chart_dict["total_unique_authors"] = total_unique_authors
    months_chart_dict["sources_total_mentions"] = \
        sources_total_mentions
    months_chart_dict["total_mentions_percentages"] = \
        total_mentions_percentages
    months_chart_dict["total_unique_authors_percentages"] = \
        total_unique_authors_percentages
    months_chart_dict["sources_total_unique_authors"] = \
        sources_total_unique_authors
    months_chart_dict["texts_dates"]=sorted(texts_dates)
# else:
#     raise Exception("Mention "+mention+" not found in dates range "+main_start_date.strftime(y_m_format)+" -> "+main_end_date.strftime(y_m_format))
# else:
#     raise Exception("Start date must be greater than end date")
    return months_chart_dict

def search_total(index: str,
                 start_date=None,
                 end_date=None,
                 **kwargs) -> int:
    """
    Search total documents that their key match their value from **kwargs.
    Args:
        index (str) : elasticsearch index name.
        **kwargs : key value sets
    Returns:
        total (int) : total searched documents.
    """
    verif = start_date is not None and end_date is not None

    s = Search(index=index)
    query_list = [{"match": {key: value}} for key, value in kwargs.items()]
    s = s.query("bool", should=query_list, minimum_should_match=len(kwargs))
    if verif:
        s = s.filter("range", date={"gte": start_date, "lte": end_date})

    total = s.count()
    return total

def save_to_elasticsearch(list_of_new_documents, index):
        print(f"Finished processing. About to save {len(list_of_new_documents)} documents to Elasticsearch.")
        start_time = time.time()
        bulk(connections.get_connection(), actions=list_of_new_documents, index=index)
        print(f"Time for saving to Elasticsearch: {time.time() - start_time:.2f} seconds")
        es_conn = connections.get_connection()
        refresh_start_time = time.time()
        es_conn.indices.refresh(index=index)
        print(f"Time for index refresh: {time.time() - refresh_start_time:.2f} seconds")
        print("list of documents in elasticsearch", list_of_new_documents)
        return list_of_new_documents
