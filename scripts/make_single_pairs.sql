#This is the code to group together the redaction pairs and select unique pairs.  It should not be reused since the table has not been created.


#looking for unique doucment pairs:
select distinct d.docID1,d.docID2 from DocumentRedaction as d  
inner join RedactOCRDoc as r on r.id = d.docId1 
inner join RedactOCRDoc as r2 on r2.id = d.docId2;


#select * from DocumentRedaction;

#select * from RedactOCRid;

#we want count for RedactOCRid.side where =2, where =1. the index into RedactOCRid.side is id. 
#RedactOCRid.id matches an id in DocumentRedaction


#This table shows how many redactions are on each side of the document pair.

create table PairCount (docID1 MEDIUMINT, docID2 MEDIUMINT, side1 tinyint, side2 tinyint);

insert into PairCount (docID1, docID2, side1, side2)
SELECT a.* FROM
(SELECT r.docID1,r.docID2,
SUM(CASE WHEN o.side = 1 THEN 1 ELSE 0 END) as side1,
SUM(CASE WHEN o.side = 2 THEN 1 ELSE 0 END) as side2
FROM DocumentRedaction r
INNER JOIN RedactOCRid o on r.id=o.id
GROUP BY r.docID1,r.docID2) a
INNER JOIN RedactOCRDoc r1 on r1.id=a.docID1
INNER JOIN RedactOCRDoc r2 on r2.id=a.docID2;


select d.docID1, d.docID2, r.id, r.side, t.redaction from 
DocumentRedaction d inner join RedactOCRid r on r.id=d.d
inner join DocumentRedactionText t on t.id = d.id;


#This table uses shows the filtered data set of filtered document pairs that havent been OCRed with a unique id for each document pair 

create table RedactOCRid (id mediumint, pairid mediumint, side tinyint);

insert into RedactOCRid (id, pairid, side)
select d.id, p.pairId, r.side from DocumentRedaction as d
inner join RedactOCRid r on d.id = r.id
inner join DPwID p on d.docId1 = p.docId1 and d.docId2 = p.docId2;


#This table filters down the data into a list of document pairs that have a unique pair associated with the document.

select s.*, d1.body as d1body, d2.body as d2body from SinglePairs s
inner join Document d1 on d1.id = s.docId1
inner join Document d2 on d2.id = s.docId2


select d.id, p.pairId, r.side from DocumentRedaction as d
inner join RedactOCRid r on d.id = r.id
inner join DPwID p on d.docId1 = p.docId1 and d.docId2 = p.docId2;

drop table SinglePairs;
create table SinglePairs (docID1 MEDIUMINT, docID2 MEDIUMINT, side1 tinyint, side2 tinyint);

LOAD DATA LOCAL INFILE '/Users/4d/Documents/declass/data/processed/RedactOCRFinalPairs.csv' INTO TABLE SinglePairs FIELDS TERMINATED BY ','OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES (docID1, docID2, side1, side2);

select * from SinglePairs;


#Because of issues with the optimizer, I had to split up the joins separately to create my final dataset table - SinglePairs

select * from PairCount;

select * from DocumentRedactionText;

select * from SinglePairs;

CREATE TABLE temp1 AS SELECT r.id, r.side, s.docId1 as d1id, s.docId2 as d2id FROM RedactOCRid r
INNER JOIN SinglePairs s on s.pairId = r.pairid;

CREATE TABLE temp2 AS SELECT t.*, drt.redaction
FROM temp1 t
INNER JOIN DocumentRedactionText drt on drt.id = t.id;

CREATE TABLE temp3 AS SELECT t.*, dr.start1, dr.end1, dr.start2, dr.end2
FROM temp2 t
INNER JOIN DocumentRedaction dr on dr.id = t.id;

select * from temp3;

CREATE TABLE temp4 as SELECT t.*, d1.body as d1body
FROM temp3 t
INNER JOIN Document d1 on d1.id = t.d1id



CREATE TABLE SinglePairSet as SELECT t.*, d2.body as d2body
FROM temp4 t
INNER JOIN Document d2 on d2.id = t.d2id

select * from SinglePairSet



#DROP TABLE temp1;
#DROP TABLE temp2;
#DROP TABLE temp3;
#DROP TABLE temp4;



##### END OF BREAKING COMMENTED PART INTO PIECES


