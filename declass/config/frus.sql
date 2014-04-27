/*Various mysql queries for the frus colletion DB*/

/* the persons table contains name information on individuals appearing in 
the FRUS docs*/
create Table if not exists persons(
    id VARCHAR(32),
    last VARCHAR(16),
    first VARCHAR(16),
    suffix VARCHAR(16),
    description MEDIUMTEXT,
    PRIMARY KEY (id)
);
    
/* the preface table contains all the preface data for each volume, indexed 
by volume */

create Table if not exists preface(
    id VARCHAR(20),
    text LONGTEXT,
    html LONGTEXT,
    PRIMARY KEY (id)
);

/* the title table contain colume title, editors and date */
create Table if not exists title(
    id VARCHAR(20),
    title TEXT,
    editors MEDIUMTEXT,
    date TEXT,
    PRIMARY KEY (id)
);

/* terms table contains all the terms which appear in the vols and their 
respective definitions*/
create Table if not exists terms(
    id VARCHAR(16),
    acronym VARCHAR(16),
    def TEXT,
    PRIMARY KEY (id),
    KEY (acronym)
);

/* refs table contains all the references for each doc*/
create Table if not exists refs(
    id VARCHAR(20),
    source TEXT,
    notes MEDIUMTEXT,
    PRIMARY KEY (id)
);

/* docs table contains all the docs and their respective info*/
create Table if not exists docs(
    id VARCHAR(20),
    title TEXT,
    date datetime,
    footnotes MEDIUMTEXT,
    body LONGTEXT,
    PRIMARY KEY (id)
);

/* person_doc table contains an entry for each person mention in a doc*/
create Table if not exists person_doc(
    pid VARCHAR(32),
    did VARCHAR(20),
    KEY (pid),
    KEY (did),
    PRIMARY KEY (pid, did)
);




