
// input grades as an object where uid points to a letter grade
var grades;

var FIRSTGRADEROW = 7;
var UIDCOL = 2;
var GRADEENTRYCOL = 5;
function inputGrades(grades) {
    var uid;
    var gradeField;
    var rowHasUid = 1;
    var rowEls = document.getElementsByTagName("tr");
    for (var row=FIRSTGRADEROW; rowHasUid > 0; row++) {
        rowEl = rowEls[row];
        cellEls = rowEl.getElementsByTagName("td");
        cellEl = cellEls[UIDCOL];
        uid = "u" + cellEl.innerText.trim().slice(1);
        gradeField = cellEls[GRADEENTRYCOL];
        try {
            gradeSelect = gradeField.getElementsByTagName("select")[0];
            console.log(gradeSelect);
            gradeSelect.value = grades[uid];
        } catch (error) {}
    }
}
