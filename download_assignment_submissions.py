from canvas_api import *

def get_assignment_submission_files(assignment_id, course_id, dl_dir='.'):
    assignment_submission_api = AssignmentSubmissionsAPI(assignment_id, course_id, TOKEN)
    assignment_submission_api.download_assignment_submission_files_parallel(dl_dir, n_jobs = 64, rm_canvas_dash_extensions=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--course_id", type=str, default="636288")
    parser.add_argument("--assignment_id", type=str, default="636288")
    parser.add_argument("--dir", type=str, default='.')
    args = parser.parse_args()

    get_assignment_submission_files(args.assignment_id, args.course_id, dl_dir=args.dir)
