| Constant | Value | Meaning |
| - | - | - |
| kAlertStdAlertOKButton | 1 | The OK push button. The default text for this push button is "OK". |
| kAlertStdAlertCancelButton | 2 | The Cancel push button (optional). The default text for this push button is "Cancel". |
| kAlertStdAlertOtherButton | 3 | A third push button (optional). The default text for this push button is "Don't Save". |
| kAlertStdAlertHelpButton | 4 | The Help push button (optional). |


# Creating Dialog Boxes

Dialog boxes may be created in one of two ways:

- Using the function GetNewDialog, which takes descriptive information about the dialog from
dialog ('DLOG') and extended dialog ('dlgx') resources. The resource ID of the 'DLOG' and
'dlgx' resources must be the same, and is passed in the first parameter of this function.

- Using NewDialog, NewColorDialog, or NewFeaturesDialog, which take descriptive information
passed in the parameters of those functions.


## Historical Note

The extended dialog resource and the NewFeaturesDialog function were introduced with OS 8 and
the Appearance Manager. NewFeaturesDialog should be used to create Appearance-compliant
dialogs. Unlike NewDialog and NewColorDialog, it has a flags parameter containing the same flags
you would set in an extended dialog resource.

If NULL is specified as the second parameter in the GetNewDialog call, GetNewDialog itself creates a non-
relocatable block for the dialog structure. Passing NULL is appropriate for modal and movable modal
dialog boxes because you should dispose of the dialog box, and hence the associated dialog structure,
when the user dismisses the dialog. However, in order to avoid heap fragmentation effects, you should
ordinarily allocate your own memory for modeless dialog box dialog structures (just as you would for
a window structure) and specify the pointer to that memory block in the second parameter of the
GetNewDialog call.

Regardless of which method is used to create the dialog, a dialog structure and a window structure
will be created, and a pointer to the dialog structure will be returned to the calling function.


# The Dialog Structure

The dialog structure created by the GetNewDialog call is defined by the data type DialogRecord:

struct DialogRecord
{

WindowRecord
window;
// Dialog's window record.

Handle

items;

// Item list resource.

TEHandle

textH;

// Current editable text item.

SInt16
editField;
// Editable text item number minus 1.

SInt16
editOpen;
// (Used internally.)

SInt16

aDefItem;
// Default push button item number.

};

typedef struct DialogRecord DialogRecord;

typedef DialogRecord *DialogPeek;

Note that the dialog structure includes a window structure field. The Dialog Manager sets the
windowKind field of this window structure to kDialogWindowKind.

<!-- PageNumber="8-12" -->
<!-- PageFooter="Version 2.2" -->
<!-- PageFooter="Dialogs and Alerts" -->