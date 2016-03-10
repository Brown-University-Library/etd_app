# -*- coding: utf-8 -*-
import os
from django.contrib.auth.models import User, Permission
from django.core.files import File
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from .test_client import ETDTestClient
from .models import Person, Candidate, CommitteeMember, Year, Department, Degree, Thesis, Keyword


LAST_NAME = u'Jonës'
FIRST_NAME = u'T©m'


def get_auth_client():
    user = User.objects.create_user('tjones@brown.edu', 'pw')
    auth_client = ETDTestClient()
    auth_client.force_login(user)
    return auth_client


def get_staff_client():
    user = User.objects.create_user('staff@brown.edu', 'pw')
    change_candidate_perm = Permission.objects.get(codename='change_candidate')
    user.user_permissions.add(change_candidate_perm)
    staff_client = ETDTestClient()
    staff_client.force_login(user)
    return staff_client


class TestStaticViews(SimpleTestCase):

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, u'<title>Electronic Theses & Dissertations at Brown University')
        self.assertContains(response, u'Ph.D. candidates at Brown must file their dissertations electronically.')
        self.assertContains(response, u'Login or Register')
        self.assertContains(response, u'Staff Login')

    def test_overview(self):
        response = self.client.get(reverse('overview'))
        self.assertContains(response, u'ETD Submission Overview')

    def test_faq(self):
        response = self.client.get(reverse('faq'))
        self.assertContains(response, u'Where are Brown’s ETDs available?')

    def test_tutorials(self):
        response = self.client.get(reverse('tutorials'))
        self.assertContains(response, u'Online Tutorials')

    def test_copyright(self):
        response = self.client.get(reverse('copyright'))
        self.assertContains(response, u'You own the copyright to your dissertation')


class CandidateCreator(object):
    '''mixin object for creating candidates'''

    @property
    def cur_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def _create_candidate(self):
        year = Year.objects.create(year=u'2016')
        self.dept = Department.objects.create(name=u'Engineering')
        degree = Degree.objects.create(abbreviation=u'Ph.D', name=u'Doctor')
        p = Person.objects.create(netid=u'tjones@brown.edu', last_name=LAST_NAME, first_name=FIRST_NAME,
                email='tom_jones@brown.edu')
        self.candidate = Candidate.objects.create(person=p, year=year, department=self.dept, degree=degree)


class TestRegister(TestCase, CandidateCreator):

    def setUp(self):
        #set an incorrect netid here, to make sure it's read from the username instead of
        #   the passed in value - we don't want someone to be able to register for a different user.
        self.person_data = {u'netid': u'wrongid@brown.edu', u'orcid': '1234567890',
                u'last_name': LAST_NAME, u'first_name': FIRST_NAME,
                u'address_street': u'123 Some Rd.', u'address_city': u'Ville',
                u'address_state': u'RI', u'address_zip': u'12345-5423',
                u'email': u'tomjones@brown.edu', u'phone': u'401-123-1234'}

    def test_register_auth(self):
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, '%s/?next=/register/' % settings.LOGIN_URL, fetch_redirect_response=False)

    def test_register_get(self):
        auth_client = get_auth_client()
        response = auth_client.get(reverse('register'))
        self.assertContains(response, u'Registration:')
        self.assertContains(response, u'Last Name')
        self.assertContains(response, u'Department')
        self.assertContains(response, u'submit')
        self.assertContains(response, u'Restrict access')
        self.assertNotContains(response, u'Netid')

    def test_register_get_candidate_exists(self):
        self._create_candidate()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('register'))
        self.assertContains(response, u'value="%s"' % LAST_NAME)
        self.assertContains(response, u'selected="selected">2016</option>')

    def _create_candidate_foreign_keys(self):
        self.year = Year.objects.create(year=u'2016')
        self.year2 = Year.objects.create(year=u'2017')
        self.dept = Department.objects.create(name=u'Engineering')
        self.degree = Degree.objects.create(abbreviation=u'Ph.D', name=u'Doctor')

    def test_new_person_and_candidate_created_with_embargo(self):
        '''verify that new data for Person & Candidate gets saved properly (& redirected to candidate_home)'''
        auth_client = get_auth_client()
        self._create_candidate_foreign_keys()
        data = self.person_data.copy()
        data.update({u'year': self.year.id, u'department': self.dept.id, u'degree': self.degree.id,
                     u'set_embargo': 'on'})
        response = auth_client.post(reverse('register'), data, follow=True)
        person = Person.objects.all()[0]
        self.assertEqual(person.netid, u'tjones@brown.edu') #make sure logged-in user netid was used, not the invalid parameter netid
        self.assertEqual(person.last_name, LAST_NAME)
        candidate = Candidate.objects.all()[0]
        self.assertEqual(candidate.year.year, u'2016')
        self.assertEqual(candidate.degree.abbreviation, u'Ph.D')
        self.assertEqual(candidate.embargo_end_year, u'2018')
        self.assertRedirects(response, reverse('candidate_home'))

    def test_no_embargo(self):
        auth_client = get_auth_client()
        self._create_candidate_foreign_keys()
        data = self.person_data.copy()
        data.update({u'year': self.year.id, u'department': self.dept.id, u'degree': self.degree.id})
        response = auth_client.post(reverse('register'), data, follow=True)
        candidate = Candidate.objects.all()[0]
        self.assertEqual(candidate.embargo_end_year, u'')

    def test_register_and_edit_existing_person_by_netid(self):
        person = Person.objects.create(netid='tjones@brown.edu', last_name=LAST_NAME)
        auth_client = get_auth_client()
        self._create_candidate_foreign_keys()
        data = self.person_data.copy()
        data['last_name'] = 'new last name'
        data.update({u'year': self.year.id, u'department': self.dept.id, u'degree': self.degree.id})
        response = auth_client.post(reverse('register'), data, follow=True)
        self.assertEqual(len(Person.objects.all()), 1)
        person = Person.objects.all()[0]
        self.assertEqual(person.last_name, 'new last name')
        self.assertEqual(len(Candidate.objects.all()), 1)
        candidate = Candidate.objects.get(person=person)
        self.assertEqual(candidate.year.year, u'2016')

    def test_register_and_edit_existing_person_by_orcid(self):
        person = Person.objects.create(orcid='1234567890', last_name=LAST_NAME)
        auth_client = get_auth_client()
        self._create_candidate_foreign_keys()
        data = self.person_data.copy()
        data['last_name'] = 'new last name'
        data.update({u'year': self.year.id, u'department': self.dept.id, u'degree': self.degree.id})
        response = auth_client.post(reverse('register'), data, follow=True)
        self.assertEqual(len(Person.objects.all()), 1)
        person = Person.objects.all()[0]
        self.assertEqual(person.last_name, 'new last name')
        self.assertEqual(len(Candidate.objects.all()), 1)
        candidate = Candidate.objects.get(person=person)
        self.assertEqual(candidate.year.year, u'2016')

    def test_edit_candidate_data(self):
        auth_client = get_auth_client()
        self._create_candidate_foreign_keys()
        person = Person.objects.create(netid='tjones@brown.edu', last_name=LAST_NAME)
        candidate = Candidate.objects.create(person=person, year=self.year, department=self.dept, degree=self.degree)
        data = self.person_data.copy()
        data['last_name'] = 'new last name'
        data.update({u'year': self.year2.id, u'department': self.dept.id, u'degree': self.degree.id})
        response = auth_client.post(reverse('register'), data, follow=True)
        self.assertEqual(len(Person.objects.all()), 1)
        person = Person.objects.all()[0]
        self.assertEqual(person.last_name, 'new last name')
        self.assertEqual(len(Candidate.objects.all()), 1)
        candidate = Candidate.objects.get(person=person)
        self.assertEqual(candidate.year.year, u'2017')


class TestCandidateHome(TestCase, CandidateCreator):

    def test_candidate_home_auth(self):
        response = self.client.get(reverse('candidate_home'))
        self.assertRedirects(response, '%s/?next=/candidate/' % settings.LOGIN_URL, fetch_redirect_response=False)

    def test_candidate_get(self):
        self._create_candidate()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_home'))
        self.assertContains(response, u'%s %s' % (FIRST_NAME, LAST_NAME))
        self.assertContains(response, u'Edit Profile</a>')
        self.assertContains(response, u'Submit/Edit information about your dissertation')
        self.assertContains(response, u'Upload dissertation file (PDF)')
        self.assertContains(response, u'Submit Cashier\'s Office receipt for dissertation fee')
        self.assertNotContains(response, u'Completed on ')

    def test_candidate_get_with_thesis(self):
        self._create_candidate()
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            pdf_file = File(f)
            self.candidate.thesis.document = pdf_file
            self.candidate.thesis.save()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_home'))
        self.assertContains(response, u'test.pdf')
        self.assertContains(response, u'Upload new dissertation file (PDF)')

    def test_candidate_get_checklist_complete(self):
        self._create_candidate()
        self.candidate.gradschool_checklist.dissertation_fee = timezone.now()
        self.candidate.gradschool_checklist.bursar_receipt = timezone.now()
        self.candidate.gradschool_checklist.gradschool_exit_survey = timezone.now()
        self.candidate.gradschool_checklist.earned_docs_survey = timezone.now()
        self.candidate.gradschool_checklist.pages_submitted_to_gradschool = timezone.now()
        self.candidate.gradschool_checklist.save()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_home'))
        self.assertContains(response, u'Completed on ')

    def test_candidate_get_committee_members(self):
        self._create_candidate()
        advisor_person = Person.objects.create(last_name='johnson', first_name='bob')
        advisor = CommitteeMember.objects.create(person=advisor_person, role='advisor', department=self.dept)
        self.candidate.committee_members.add(advisor)
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_home'))
        self.assertContains(response, 'Advisor')

    def test_candidate_get_not_registered(self):
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_home'))
        self.assertRedirects(response, reverse('register'))

    def test_candidate_submit(self):
        self._create_candidate()
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            pdf_file = File(f)
            self.candidate.thesis.document = pdf_file
            self.candidate.thesis.save()
        thesis = self.candidate.thesis
        thesis.title = u'test'
        thesis.abstract = u'abstract'
        thesis.keywords.add(Keyword.objects.create(text=u'test'))
        thesis.save()
        auth_client = get_auth_client()
        response = auth_client.post(reverse('candidate_submit'))
        self.assertRedirects(response, 'http://testserver/candidate/')
        self.assertEqual(Candidate.objects.all()[0].thesis.status, 'pending')


class TestCandidateUpload(TestCase, CandidateCreator):

    def test_upload_auth(self):
        response = self.client.get(reverse('candidate_upload'))
        self.assertRedirects(response, '%s/?next=/candidate/upload/' % settings.LOGIN_URL, fetch_redirect_response=False)

    def test_upload_get(self):
        self._create_candidate()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_upload'))
        self.assertContains(response, u'%s %s' % (FIRST_NAME, LAST_NAME))
        self.assertContains(response, u'Upload Your Dissertation')

    def test_upload_post(self):
        self._create_candidate()
        auth_client = get_auth_client()
        self.assertEqual(len(Thesis.objects.all()), 1)
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            response = auth_client.post(reverse('candidate_upload'), {'thesis_file': f})
            self.assertEqual(len(Thesis.objects.all()), 1)
            self.assertEqual(Candidate.objects.all()[0].thesis.file_name, 'test.pdf')
            self.assertRedirects(response, reverse('candidate_home'))

    def test_upload_bad_file(self):
        self._create_candidate()
        auth_client = get_auth_client()
        self.assertEqual(len(Thesis.objects.all()), 1)
        with open(os.path.join(self.cur_dir, 'test_files', 'test_obj'), 'rb') as f:
            response = auth_client.post(reverse('candidate_upload'), {'thesis_file': f})
            self.assertContains(response, u'Upload Your Dissertation')
            self.assertContains(response, u'file must be a PDF')
            self.assertFalse(Candidate.objects.all()[0].thesis.document)
            self.assertEqual(len(Thesis.objects.all()), 1)

    def test_upload_new_thesis_file(self):
        self._create_candidate()
        auth_client = get_auth_client()
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            pdf_file = File(f)
            self.candidate.thesis.document = pdf_file
            self.candidate.thesis.save()
        self.assertEqual(len(Thesis.objects.all()), 1)
        thesis = Candidate.objects.all()[0].thesis
        self.assertEqual(thesis.file_name, 'test.pdf')
        self.assertEqual(thesis.checksum, 'b1938fc5549d1b5b42c0b695baa76d5df5f81ac3')
        with open(os.path.join(self.cur_dir, 'test_files', 'test2.pdf'), 'rb') as f:
            response = auth_client.post(reverse('candidate_upload'), {'thesis_file': f})
            self.assertEqual(len(Thesis.objects.all()), 1)
            thesis = Candidate.objects.all()[0].thesis
            self.assertEqual(thesis.file_name, 'test2.pdf')
            self.assertEqual(thesis.checksum, '2ce252ec827258837e53b2b0bfb94141ba951f2e')


class TestCandidateMetadata(TestCase, CandidateCreator):

    def test_metadata_auth(self):
        response = self.client.get(reverse('candidate_metadata'))
        self.assertRedirects(response, '%s/?next=/candidate/metadata/' % settings.LOGIN_URL, fetch_redirect_response=False)

    def test_metadata_get(self):
        self._create_candidate()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_metadata'))
        self.assertContains(response, u'%s %s' % (FIRST_NAME, LAST_NAME))
        self.assertContains(response, u'About Your Dissertation')
        self.assertContains(response, u'Title')

    def test_metadata_post(self):
        self._create_candidate()
        auth_client = get_auth_client()
        self.assertEqual(len(Thesis.objects.all()), 1)
        k = Keyword.objects.create(text=u'tëst')
        data = {'title': u'tëst', 'abstract': u'tëst abstract', 'keywords': k.id}
        response = auth_client.post(reverse('candidate_metadata'), data)
        self.assertRedirects(response, reverse('candidate_home'))
        self.assertEqual(len(Thesis.objects.all()), 1)
        self.assertEqual(Candidate.objects.all()[0].thesis.title, u'tëst')

    def test_metadata_post_thesis_already_exists(self):
        self._create_candidate()
        auth_client = get_auth_client()
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            pdf_file = File(f)
            self.candidate.thesis.document = pdf_file
            self.candidate.thesis.save()
        self.assertEqual(len(Thesis.objects.all()), 1)
        k = Keyword.objects.create(text=u'tëst')
        data = {'title': u'tëst', 'abstract': u'tëst abstract', 'keywords': k.id}
        response = auth_client.post(reverse('candidate_metadata'), data)
        self.assertEqual(len(Thesis.objects.all()), 1)
        thesis = Candidate.objects.all()[0].thesis
        self.assertEqual(thesis.title, u'tëst')
        self.assertEqual(thesis.file_name, u'test.pdf')


class TestCommitteeMembers(TestCase, CandidateCreator):

    def test_committee_members_auth(self):
        response = self.client.get(reverse('candidate_committee'))
        self.assertRedirects(response, '%s/?next=/candidate/committee/' % settings.LOGIN_URL, fetch_redirect_response=False)

    def test_committee_members_get(self):
        self._create_candidate()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('candidate_committee'))
        self.assertContains(response, u'About Your Committee')
        self.assertContains(response, u'Last Name')
        self.assertContains(response, u'Brown Department')

    def test_committee_members_post(self):
        self._create_candidate()
        auth_client = get_auth_client()
        post_data = {'last_name': 'smith', 'first_name': 'bob', 'role': 'reader', 'department': self.dept.id}
        response = auth_client.post(reverse('candidate_committee'), post_data)
        self.assertEqual(Candidate.objects.all()[0].committee_members.all()[0].person.last_name, 'smith')
        self.assertEqual(Candidate.objects.all()[0].committee_members.all()[0].role, 'reader')


class TestStaffReview(TestCase, CandidateCreator):

    def test_login_required(self):
        response = self.client.get(reverse('staff_home'))
        self.assertRedirects(response, '%s/?next=/review/' % settings.LOGIN_URL, fetch_redirect_response=False)

    def test_permission_required(self):
        auth_client = get_auth_client()
        response = auth_client.get(reverse('staff_home'))
        self.assertEqual(response.status_code, 403)

    def test_staff_home_get(self):
        staff_client = get_staff_client()
        response = staff_client.get(reverse('staff_home'))
        self.assertContains(response, u'View candidates by status')

    def test_view_candidates_permission_required(self):
        auth_client = get_auth_client()
        response = auth_client.get(reverse('review_candidates', kwargs={'status': 'all'}))
        self.assertEqual(response.status_code, 403)

    def test_view_candidates_all(self):
        self._create_candidate()
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            pdf_file = File(f)
            self.candidate.thesis.document = pdf_file
            self.candidate.thesis.save()
        thesis = Thesis.objects.all()[0]
        thesis.title = u'test'
        thesis.abstract = u'abstract'
        thesis.keywords.add(Keyword.objects.create(text=u'test'))
        thesis.save()
        thesis.submit()
        staff_client = get_staff_client()
        response = staff_client.get(reverse('review_candidates', kwargs={'status': 'all'}))
        self.assertContains(response, u'Candidate</th><th>Department</th><th>Status</th>')
        self.assertContains(response, u'%s, %s' % (LAST_NAME, FIRST_NAME))
        self.assertContains(response, u'Awaiting ')

    def test_view_candidates_in_progress(self):
        self._create_candidate()
        self.candidate.thesis.title = u'tëst'
        self.candidate.thesis.save()
        staff_client = get_staff_client()
        response = staff_client.get(reverse('review_candidates', kwargs={'status': 'in_progress'}))
        self.assertContains(response, u'Candidate</th><th>Department</th><th>Dissertation Title</th>')
        self.assertContains(response, u'tëst')

    def test_view_candidates_other_statuses(self):
        staff_client = get_staff_client()
        response = staff_client.get(reverse('review_candidates', kwargs={'status': 'awaiting_gradschool'}))
        self.assertEqual(response.status_code, 200)
        response = staff_client.get(reverse('review_candidates', kwargs={'status': 'dissertation_rejected'}))
        self.assertEqual(response.status_code, 200)
        response = staff_client.get(reverse('review_candidates', kwargs={'status': 'paperwork_incomplete'}))
        self.assertEqual(response.status_code, 200)
        response = staff_client.get(reverse('review_candidates', kwargs={'status': 'complete'}))
        self.assertEqual(response.status_code, 200)


class TestStaffApproveThesis(TestCase, CandidateCreator):

    def test_permission_required(self):
        self._create_candidate()
        auth_client = get_auth_client()
        response = auth_client.get(reverse('approve', kwargs={'candidate_id': self.candidate.id}))
        self.assertEqual(response.status_code, 403)

    def test_approve_get(self):
        self._create_candidate()
        staff_client = get_staff_client()
        response = staff_client.get(reverse('approve', kwargs={'candidate_id': self.candidate.id}))
        self.assertContains(response, u'%s %s' % (FIRST_NAME, LAST_NAME))
        self.assertContains(response, u'<input type="checkbox" name="dissertation_fee" />Received')
        self.assertContains(response, u'Title page issue')
        self.assertNotContains(response, 'Received on ')
        now = timezone.now()
        self.candidate.gradschool_checklist.dissertation_fee = now
        self.candidate.gradschool_checklist.save()
        response = staff_client.get(reverse('approve', kwargs={'candidate_id': self.candidate.id}))
        self.assertNotContains(response, u'<input type="checkbox" name="dissertation_fee" />Received')
        self.assertContains(response, 'Received on ')

    def test_approve_post(self):
        staff_client = get_staff_client()
        self._create_candidate()
        self.candidate.gradschool_checklist.earned_docs_survey = timezone.now()
        self.candidate.gradschool_checklist.save()
        post_data = {'dissertation_fee': True, 'bursar_receipt': True}
        response = staff_client.post(reverse('approve', kwargs={'candidate_id': self.candidate.id}), post_data)
        self.assertEqual(Candidate.objects.all()[0].gradschool_checklist.dissertation_fee.date(), timezone.now().date())
        self.assertEqual(Candidate.objects.all()[0].gradschool_checklist.bursar_receipt.date(), timezone.now().date())
        self.assertEqual(Candidate.objects.all()[0].gradschool_checklist.earned_docs_survey.date(), timezone.now().date())
        self.assertRedirects(response, reverse('staff_home'))

    def test_format_post_perms(self):
        self._create_candidate()
        auth_client = get_auth_client()
        response = auth_client.post(reverse('format_post', kwargs={'candidate_id': self.candidate.id}))
        self.assertEqual(response.status_code, 403)

    def test_format_post(self):
        self._create_candidate()
        thesis = self.candidate.thesis
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            pdf_file = File(f)
            thesis.document = pdf_file
            thesis.title = 'Test'
            thesis.abstract = 'test abstract'
            thesis.save()
            thesis.keywords.add(Keyword.objects.create(text=u'test'))
        self.candidate.thesis.submit()
        staff_client = get_staff_client()
        post_data = {'title_page_issue': True, 'signature_page_issue': True, 'signature_page_comment': 'Test comment',
                'accept_diss': 'Approve'}
        url = reverse('format_post', kwargs={'candidate_id': self.candidate.id})
        response = staff_client.post(url, post_data)
        self.assertRedirects(response, reverse('approve', kwargs={'candidate_id': self.candidate.id}))
        self.assertEqual(Candidate.objects.all()[0].thesis.format_checklist.title_page_issue, True)
        self.assertEqual(Candidate.objects.all()[0].thesis.status, 'accepted')

    def test_format_post_reject(self):
        self._create_candidate()
        thesis = self.candidate.thesis
        with open(os.path.join(self.cur_dir, 'test_files', 'test.pdf'), 'rb') as f:
            pdf_file = File(f)
            thesis.document = pdf_file
            thesis.title = 'Test'
            thesis.abstract = 'test abstract'
            thesis.save()
            thesis.keywords.add(Keyword.objects.create(text=u'test'))
        self.candidate.thesis.submit()
        staff_client = get_staff_client()
        post_data = {'title_page_issue': True, 'signature_page_issue': True, 'signature_page_comment': 'Test comment',
                'reject_diss': 'Reject'}
        url = reverse('format_post', kwargs={'candidate_id': self.candidate.id})
        response = staff_client.post(url, post_data)
        self.assertEqual(Candidate.objects.all()[0].thesis.status, 'rejected')