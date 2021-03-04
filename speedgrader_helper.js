LOAD_TIME = 4000;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function which_student() {
    var student_n_el = document.getElementById("x_of_x_students_frd")
    return parseInt(student_n_el.innerHTML.split("/")[0].trim());
}

function leave_comment(q_id, comment, parent) {
    var comment_el = parent.querySelectorAll('[name="question_comment_' + q_id + '"]')[0];
    comment_el.innerHTML = comment;
}

async function submit_scores(iframe) {
    var submitter = iframe.getElementsByClassName("update-scores")[0];
    submitter.click();
    await sleep(LOAD_TIME);
}

function get_question_element(q_id, parent) { return parent.getElementById("question_" + q_id); }

function full_credit(q_id, comment, parent) {
    var question_el = get_question_element(q_id, parent);
    var points_possible = parseInt(
        question_el.getElementsByClassName("question_points")[0].innerHTML.split("/")[1].trim());
    var points_earned_el = question_el.getElementsByClassName("question_input_hidden")[0];
    points_earned_el.value = points_possible;
    leave_comment(q_id, comment, parent);
}
function full_credit_multiple(q_ids, comments, iframe) {
    var q_id, char_limit, comment;
    for (var i = 0; i < q_ids.length; i++) {
        q_id = q_ids[i];
	comment = comments[i];
        full_credit(q_id, comment, iframe);
    }
}

var CONTINUE_KEY = 220;
var continuing = false;
function handle_continue_key(e) {
    if (e.keyCode == CONTINUE_KEY & continuing == false) {
        continuing = true;
    }
}
if (document.addEventListener) {
    document.addEventListener('keydown', handle_continue_key, false);
}
else if (document.attachEvent) {
    document.attachEvent('onkeydown', handle_continue_key);
}
async function investigate_under_char_limit(q_id, char_limit, comment, parent) {
    var question_el = get_question_element(q_id, parent);
    var answer = question_el.getElementsByClassName("quiz_response_text")[0].innerText.trim();
    if (answer.length < char_limit) {
        question_el.scrollIntoView();
        while (!continuing) {
            await sleep(50);
        }
        continuing = false;
    } else {
        full_credit(q_id, comment, parent);
    }
}
async function investigate_under_char_limit_multiple(q_ids, char_limits, comments, iframe) {
    var q_id, char_limit, comment;
    for (var i = 0; i < q_ids.length; i++) {
        q_id = q_ids[i];
        char_limit = char_limits[i];
        comment = comments[i];
        await investigate_under_char_limit(q_id, char_limit, comment, iframe);
    }
}

async function fix_broken_fill_in_blank(q_id, which_blank, worth, correct_answer, comment, parent) {
    var question_el = get_question_element(q_id, parent);
    var current_points_el = question_el.getElementsByClassName("question_input_hidden")[0];
    var answer = question_el.getElementsByClassName("question_input")[which_blank + 1].value;
    console.log(answer);
    console.log(current_points_el);
    if (answer == correct_answer) {
        current_points_el.value = (parseFloat(current_points_el.value) + worth).toString();
    }
    console.log(current_points_el);
    leave_comment(q_id, comment, parent);
}

// f takes the iframe as an argument
async function all_students_apply(f, score_updates=true) {
    var first_student = which_student();
    var this_student = first_student;
    var next, iframe;
    do {
        next = document.getElementById("next-student-button");
        try {
            iframe = document.getElementById("speedgrader_iframe").contentWindow.document
            await f(iframe);
            if (score_updates) {
                await submit_scores(iframe);
            }
        } catch (err) { 
            console.log(err); 
        } finally {
            next.click();
            await sleep(LOAD_TIME);
            this_student = which_student();
        }

    } while (this_student != first_student);

}

async function give_max_points(question_ids, comments) {
    await all_students_apply(full_credit_multiple.bind(null, question_ids, comments));    
}
async function investigate_essays(question_ids, char_limits, comments) {
    await all_students_apply(investigate_under_char_limit_multiple.bind(null, question_ids, char_limits, comments));    
}
async function fix_broken_fill_in_blank_all(q_id, which_blank, worth, correct_answer, comment) {
    await all_students_apply(fix_broken_fill_in_blank.bind(null, q_id, which_blank, worth, correct_answer, comment));
}