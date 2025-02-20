
import os, json, argparse, time
from multiprocessing import Pool

import simple_wikidata_db.utils as utils

from bootleg_data_prep.language import ENSURE_ASCII

INSTANCE_OF_PROP = "P31"
DISAMBIG_PAGE = {"Q4167410", "Q22808320"}

def get_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type = str, default = '/lfs/raiders8/0/lorr1/wikidata', help = 'path to output directory')
    parser.add_argument('--out_dir', type = str, default = 'disambig_qids', help = 'path to output directory')
    parser.add_argument('--processes', type = int, default = 10, help = "Number of concurrent processes to spin off. ")
    return parser 


def launch_entity_table(entity_files, args):
    print(f"Starting with {args.processes} processes")
    pool = Pool(processes = args.processes)
    messages = [(i, len(entity_files), entity_files[i]) for i in range(len(entity_files))]
    res = pool.map(load_entity_file, messages, chunksize=1)
    return res

def load_entity_file(message):
    start = time.time()
    job_index, num_jobs, filename = message
    ids = set()
    for triple in utils.jsonl_generator(filename):
        qid, property_id, value = triple['qid'], triple['property_id'], triple['value']
        if property_id == INSTANCE_OF_PROP and value in DISAMBIG_PAGE:
            ids.add(qid)

    print(f"Finished {job_index} / {num_jobs}...{filename}. Fetched types for {len(ids)} entities. {time.time() - start} seconds.")
    return ids

def main():
    start = time.time()
    args = get_arg_parser().parse_args()

    out_dir = os.path.join(args.data, args.out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    fdir = os.path.join(args.data, "processed_batches", "entity_rels")
    external_tables = utils.get_batch_files(fdir)
    all_ids = launch_entity_table(external_tables, args)

    final_ids = set()
    for id in all_ids:
        final_ids.update(id)

    out_fpath = os.path.join(out_dir, 'disambig_qids.json')
    with open(out_fpath, 'w', encoding='utf8') as out_file:
        out_file.write(json.dumps(final_ids, ensure_ascii=ENSURE_ASCII) + "\n")
    print(f"Written {len(final_ids)} to {out_file} in {time.time()-start}")
    
    


if __name__ == "__main__":
    main()