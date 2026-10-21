// A disposable app. These notes exist only in this browser page.
const notes = [
  {text:'Buy bread and coffee',when:'Monday'},
  {text:'Call the plumber',when:'Tuesday'},
  {text:'Book a table for Friday',when:'Wednesday'},
];
const list=document.querySelector('#list'), query=document.querySelector('#q');
function show(){
  const hits=notes.filter(note=>note.text.toLowerCase().includes(query.value.trim().toLowerCase()));
  list.replaceChildren(...hits.map(note=>{
    const row=document.createElement('li'), date=document.createElement('small');
    row.append(document.createTextNode(note.text));date.textContent=note.when;row.append(date);return row;
  }));
  document.querySelector('#count').textContent=hits.length+(hits.length===1?' note':' notes');
  document.querySelector('#empty').hidden=hits.length!==0;
}
document.querySelector('#add').addEventListener('submit',event=>{
  event.preventDefault();const field=document.querySelector('#text');
  if(field.value.trim())notes.unshift({text:field.value.trim(),when:'Just now'});
  field.value='';show();
});
query.addEventListener('input',show);show();
